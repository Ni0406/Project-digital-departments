# datacollector/management/commands/collect_data.py
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import telegram
import asyncio  # <--- НОВОЕ: Импортируем asyncio
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datacollector.models import Ticker, StockData, NewsArticle
from decimal import Decimal, ROUND_DOWN
from django.db import transaction

# Список тикеров, которые мы хотим отслеживать
TARGET_TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA"]

# Порог изменения цены в процентах для срабатывания алерта
ALERT_THRESHOLD = 0.5  # Временно установим низкий порог для тестирования


class Command(BaseCommand):
    help = 'Собирает данные по акциям и новости, а также проверяет на предмет алертов.'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Инициализируем бота один раз при создании команды
        self.bot = telegram.Bot(token=settings.TELEGRAM_BOT_TOKEN)

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Начинаем сбор данных...'))
        self.collect_stock_prices()
        self.stdout.write(self.style.SUCCESS('Сбор данных успешно завершен!'))

    # <--- ИЗМЕНЕНИЕ ЗДЕСЬ: Метод send_telegram_alert стал async
    async def send_telegram_alert(self, message):
        """Отправляет сообщение в заданный чат Telegram."""
        try:
            # <--- ИЗМЕНЕНИЕ ЗДЕСЬ: Добавлено await
            await self.bot.send_message(
                chat_id=settings.TELEGRAM_CHAT_ID,
                text=message,
                parse_mode='HTML'
            )
            self.stdout.write(self.style.SUCCESS(f'Отправлен алерт: {message}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Ошибка при отправке сообщения в Telegram: {e}'))
            import traceback
            traceback.print_exc()

    def check_price_alert(self, ticker_obj):
        """Проверяет последние данные по акции на предмет резкого изменения цены."""
        latest_data = StockData.objects.filter(ticker=ticker_obj).order_by('-date')[:2]

        if len(latest_data) < 2:
            return

        today_data = latest_data[0]
        yesterday_data = latest_data[1]

        price_today = today_data.close_price
        price_yesterday = yesterday_data.close_price

        if price_yesterday == Decimal('0'):
            return

        change_percent = ((price_today - price_yesterday) / price_yesterday) * Decimal('100')

        if abs(change_percent) >= Decimal(str(ALERT_THRESHOLD)):
            direction = "📈 РОСТ" if change_percent > 0 else "📉 ПАДЕНИЕ"

            message = (
                f"<b>🚨 Внимание! Резкое изменение цены для {ticker_obj.symbol}</b>\n\n"
                f"{direction}\n\n"
                f"Изменение за день: <b>{change_percent.quantize(Decimal('0.01'), rounding=ROUND_DOWN)}%</b>\n"
                f"Цена вчера: ${price_yesterday.quantize(Decimal('0.01'), rounding=ROUND_DOWN)}\n"
                f"Цена сегодня: <b>${price_today.quantize(Decimal('0.01'), rounding=ROUND_DOWN)}</b>"
            )
            # <--- ИЗМЕНЕНИЕ ЗДЕСЬ: Используем asyncio.run() для вызова асинхронной функции
            asyncio.run(self.send_telegram_alert(message))

    def collect_stock_prices(self):
        """Собирает и сохраняет исторические данные о ценах акций."""
        self.stdout.write('Сбор данных о ценах акций...')
        for symbol in TARGET_TICKERS:
            ticker_obj, created = Ticker.objects.get_or_create(symbol=symbol)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Создан новый тикер: {symbol}'))
            else:
                self.stdout.write(f'Тикер {symbol} уже существует в БД.')

            try:
                data = yf.download(symbol, period="5d", auto_adjust=True)

                if data.empty:
                    self.stdout.write(self.style.WARNING(f'Нет данных из yfinance для {symbol} в заданном диапазоне.'))
                    continue

                self.stdout.write(f"Данные из yfinance для {symbol} получены. {len(data)} строк.")

                with transaction.atomic():
                    for index, row in data.iterrows():
                        try:
                            open_p = float(row['Open'].item())
                            high_p = float(row['High'].item())
                            low_p = float(row['Low'].item())
                            close_p = float(row['Close'].item())
                            volume_val = int(row['Volume'].item())
                        except (ValueError, KeyError, AttributeError) as ve:
                            self.stderr.write(self.style.ERROR(
                                f"Ошибка преобразования/отсутствие колонки для {symbol} на {index.date()}: {ve} - Пропускаем строку."))
                            continue

                        StockData.objects.update_or_create(
                            ticker=ticker_obj,
                            date=index.date(),
                            defaults={
                                'open_price': Decimal(str(open_p)),
                                'high_price': Decimal(str(high_p)),
                                'low_price': Decimal(str(low_p)),
                                'close_price': Decimal(str(close_p)),
                                'volume': volume_val
                            }
                        )

                self.stdout.write(self.style.SUCCESS(f'Данные для {symbol} обновлены/созданы.'))

                self.check_price_alert(ticker_obj)

            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Глобальная ошибка при сборе данных для {symbol}: {e}'))
                import traceback
                traceback.print_exc()

    def collect_market_news(self):
        """Парсит и сохраняет финансовые новости."""
        self.stdout.write('Сбор новостей...')
        url = "https://www.marketwatch.com/latest-news"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = soup.find_all('div', class_='article__content')
            news_to_create = []
            for article in articles:
                headline_tag = article.find('a', class_='link')
                if not headline_tag:
                    continue
                headline = headline_tag.get_text(strip=True)
                link = headline_tag['href']
                if not NewsArticle.objects.filter(url=link).exists():
                    news_to_create.append(
                        NewsArticle(
                            headline=headline,
                            url=link,
                            source='MarketWatch'
                        )
                    )
            if news_to_create:
                with transaction.atomic():
                    NewsArticle.objects.bulk_create(news_to_create)
                self.stdout.write(self.style.SUCCESS(f'Сохранено {len(news_to_create)} новых новостей.'))
            else:
                self.stdout.write('Новых новостей не найдено.')

        except requests.exceptions.RequestException as e:
            self.stderr.write(self.style.ERROR(f'Ошибка при парсинге новостей: {e}'))
            self.stderr.write(self.style.WARNING(
                "Возможно, MarketWatch блокирует запросы. Сбор новостей пропущен. Попробуйте другой источник или более продвинутый метод парсинга (например, с использованием прокси)."))
            import traceback
            traceback.print_exc()