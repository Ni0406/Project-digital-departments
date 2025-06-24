# analytics/views.py

from django.shortcuts import render
from django.http import Http404
from datacollector.models import Ticker
from . import services
import json


def dashboard_view(request, ticker_symbol):
    """
    Отображает дашборд с аналитикой и графиками для указанного тикера.
    """
    try:
        # Проверяем, существует ли такой тикер в нашей базе
        ticker = Ticker.objects.get(symbol__iexact=ticker_symbol)
    except Ticker.DoesNotExist:
        raise Http404("Такой тикер не найден в базе данных")

    # 1. Получаем данные для карточек с ключевыми метриками
    dynamics_30_days = services.calculate_price_dynamics(ticker.symbol, days=30)
    avg_price_90_days = services.calculate_average_price(ticker.symbol, days=90)
    min_max_365_days = services.get_min_max_prices(ticker.symbol, days=365)

    # 2. Готовим данные для графика динамики цен
    stock_data_for_chart = services.get_stock_data_for_period(ticker.symbol, days=365)

    # Преобразуем данные в формат, понятный для Chart.js (списки)
    chart_labels = [data.date.strftime('%Y-%m-%d') for data in stock_data_for_chart]
    chart_data = [float(data.close_price) for data in stock_data_for_chart]

    context = {
        'ticker': ticker,
        'dynamics_30_days': dynamics_30_days,
        'avg_price_90_days': avg_price_90_days,
        'min_max_365_days': min_max_365_days,
        # Передаем данные для графика, преобразовав их в JSON-строку
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }

    return render(request, 'analytics/dashboard.html', context)


def homepage_view(request):
    """
    Отображает главную страницу со списком всех доступных для анализа тикеров.
    """
    # Получаем все тикеры из базы данных и сортируем их по символу
    all_tickers = Ticker.objects.all().order_by('symbol')

    context = {
        'tickers': all_tickers,
    }
    return render(request, 'analytics/homepage.html', context)