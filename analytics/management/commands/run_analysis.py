# analytics/management/commands/run_analysis.py

from django.core.management.base import BaseCommand
from analytics import services

class Command(BaseCommand):
    help = "Запускает тестовый анализ данных по акциям для демонстрации"

    def handle(self, *args, **kwargs):
        # Выбираем тикер для анализа. Убедитесь, что данные для него собраны.
        ticker_to_analyze = "MSFT"

        self.stdout.write(self.style.SUCCESS(f"--- Запуск анализа для тикера {ticker_to_analyze} ---"))

        # 1. Расчет средней цены
        avg_price = services.calculate_average_price(ticker_to_analyze, days=30)
        if avg_price is not None:
            self.stdout.write(f"Средняя цена закрытия за последние 30 дней: ${avg_price:.2f}")
        else:
            self.stdout.write(self.style.WARNING("Недостаточно данных для расчета средней цены."))

        # 2. Анализ динамики цен
        dynamics = services.calculate_price_dynamics(ticker_to_analyze, days=90)
        if dynamics:
            self.stdout.write(f"\nАнализ динамики за последние 90 дней:")
            self.stdout.write(f"  - Цена на начало периода ({dynamics['start_date']}): ${dynamics['start_price']:.2f}")
            self.stdout.write(f"  - Цена на конец периода ({dynamics['end_date']}): ${dynamics['end_price']:.2f}")
            self.stdout.write(
                self.style.SUCCESS(
                    f"  - Изменение: {dynamics['absolute_change']:.2f}$ ({dynamics['percentage_change']:.2f}%)"
                )
            )
        else:
            self.stdout.write(self.style.WARNING("Недостаточно данных для анализа динамики."))

        # 3. Нахождение минимума и максимума за год
        min_max = services.get_min_max_prices(ticker_to_analyze, days=365)
        if min_max and min_max['min_price'] is not None:
            self.stdout.write(f"\nСтатистика за последний год:")
            self.stdout.write(f"  - Минимальная цена: ${min_max['min_price']:.2f}")
            self.stdout.write(f"  - Максимальная цена: ${min_max['max_price']:.2f}")
        else:
            self.stdout.write(self.style.WARNING("Недостаточно данных для расчета min/max."))