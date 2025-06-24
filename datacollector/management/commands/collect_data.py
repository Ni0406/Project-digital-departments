# datacollector/management/commands/collect_data.py
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils import timezone
from datacollector.models import Ticker, StockData, NewsArticle
from decimal import Decimal
from django.db import transaction  # Импортируем для обеспечения целостности данных

# Список тикеров, которые мы хотим отслеживать
TARGET_TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]


class Command(BaseCommand):
    help = 'Собирает данные по акциям и новости с финансовых сайтов'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Начинаем сбор данных...'))
        self.collect_stock_prices()
        self.collect_market_news()
        self.stdout.write(self.style.SUCCESS('Сбор данных успешно завершен!'))

    def collect_stock_prices(self):
        """Собирает и сохраняет исторические данные о ценах акций."""
        self.stdout.write('Сбор данных о ценах акций...')
        for symbol in TARGET_TICKERS:
            self.stdout.write(f"Попытка обработки тикера: {symbol}")
            try:
                # Получаем или создаем объект тикера в БД
                ticker_obj, created = Ticker.objects.get_or_create(symbol=symbol)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Создан новый тикер в БД: {symbol}'))
                else:
                    self.stdout.write(f'Тикер {symbol} уже существует в БД.')

                # Загружаем данные с yfinance
                # Используем auto_adjust=True по умолчанию, yfinance сам скорректирует данные
                # end=None означает текущую дату
                data = yf.download(symbol, start="2023-01-01", end=None)

                self.stdout.write(f"Данные из yfinance для {symbol} получены. Пустые ли данные? {data.empty}")
                if not data.empty:
                    self.stdout.write(f"Первые 5 строк данных для {symbol}:\n{data.head()}")
                else:
                    self.stdout.write(self.style.WARNING(f'Нет данных из yfinance для {symbol} в заданном диапазоне.'))
                    continue

                stock_data_to_create = []
                for index, row in data.iterrows():
                    # Проверяем наличие ключевых колонок и преобразуем к float для безопасности,
                    # затем к Decimal через строковое представление для точности.
                    try:
                        open_p = float(row['Open'])
                        high_p = float(row['High'])
                        low_p = float(row['Low'])
                        close_p = float(row['Close'])
                        volume_val = int(row['Volume'])
                    except (ValueError, KeyError) as ve:
                        self.stdout.write(self.style.ERROR(
                            f"Ошибка преобразования/отсутствие колонки для {symbol} на {index.date()}: {ve} - Пропускаем строку."))
                        continue

                    stock_data_to_create.append(
                        StockData(
                            ticker=ticker_obj,
                            date=index.date(),
                            open_price=Decimal(str(open_p)),
                            high_price=Decimal(str(high_p)),
                            low_price=Decimal(str(low_p)),
                            close_price=Decimal(str(close_p)),
                            volume=volume_val
                        )
                    )

                self.stdout.write(
                    f"Подготовлено {len(stock_data_to_create)} записей для массового создания для {symbol}.")

                # Используем bulk_create с ignore_conflicts для эффективности и избежания дубликатов
                # transaction.atomic() гарантирует, что либо все записи сохранятся, либо ни одна.
                with transaction.atomic():
                    # bulk_create возвращает список созданных объектов, len() даст их количество
                    created_objects = StockData.objects.bulk_create(stock_data_to_create, ignore_conflicts=True)
                    self.stdout.write(self.style.SUCCESS(
                        f'Массово сохранено {len(created_objects)} НОВЫХ записей для {symbol} (или игнорировано столько же дубликатов).'))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Глобальная ошибка при сборе данных для {symbol}: {e}'))
                import traceback
                traceback.print_exc()  # Выводим полный traceback для отладки

    def collect_market_news(self):
        """Парсит и сохраняет финансовые новости."""
        self.stdout.write('Сбор новостей...')
        url = "https://www.marketwatch.com/latest-news"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Это вызовет исключение для HTTP ошибок (например, 401 Forbidden)
            soup = BeautifulSoup(response.text, 'html.parser')
            # Селекторы могут потребовать обновления, если сайт изменит структуру
            articles = soup.find_all('div', class_='article__content')
            news_to_create = []
            for article in articles:
                headline_tag = article.find('a', class_='link')
                if not headline_tag:
                    continue
                headline = headline_tag.get_text(strip=True)
                link = headline_tag['href']
                # Проверяем, не существует ли уже новость с таким URL
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
            traceback.print_exc()  # Выводим полный traceback для отладки