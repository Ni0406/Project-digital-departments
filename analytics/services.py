# analytics/services.py

from datetime import date, timedelta
from django.db.models import Avg, Max, Min, F
from django.core.exceptions import ObjectDoesNotExist
from datacollector.models import Ticker, StockData

def get_stock_data_for_period(ticker_symbol: str, days: int):
    """Вспомогательная функция для получения данных за период."""
    try:
        ticker = Ticker.objects.get(symbol__iexact=ticker_symbol)
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        return StockData.objects.filter(
            ticker=ticker,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')

    except ObjectDoesNotExist:
        return StockData.objects.none() # Возвращаем пустой QuerySet, если тикер не найден

def calculate_average_price(ticker_symbol: str, days: int = 30) -> float | None:
    """Рассчитывает среднюю цену закрытия для тикера за N дней."""
    queryset = get_stock_data_for_period(ticker_symbol, days)

    if not queryset.exists():
        return None

    # .aggregate() возвращает словарь. Мы извлекаем из него значение.
    result = queryset.aggregate(average_price=Avg('close_price'))
    return result.get('average_price')

def calculate_price_dynamics(ticker_symbol: str, days: int = 30) -> dict | None:
    """
    Рассчитывает динамику цены (абсолютное и процентное изменение) за N дней.
    """
    queryset = get_stock_data_for_period(ticker_symbol, days)

    if queryset.count() < 2: # Нужно как минимум 2 точки для расчета динамики
        return None

    first_day_data = queryset.first()
    last_day_data = queryset.last()

    start_price = first_day_data.open_price # Цена открытия в первый день периода
    end_price = last_day_data.close_price # Цена закрытия в последний день

    absolute_change = end_price - start_price
    percentage_change = (absolute_change / start_price) * 100 if start_price != 0 else 0

    return {
        'start_date': first_day_data.date,
        'end_date': last_day_data.date,
        'start_price': start_price,
        'end_price': end_price,
        'absolute_change': absolute_change,
        'percentage_change': percentage_change,
    }

def get_min_max_prices(ticker_symbol: str, days: int = 365) -> dict | None:
    """Находит минимальную и максимальную цену для тикера за N дней."""
    queryset = get_stock_data_for_period(ticker_symbol, days)

    if not queryset.exists():
        return None

    # .aggregate() может выполнять несколько вычислений за один запрос к БД
    result = queryset.aggregate(
        min_price=Min('low_price'),
        max_price=Max('high_price')
    )
    return result