# datacollector/admin.py

from django.contrib import admin
from .models import Ticker, StockData, NewsArticle

@admin.register(Ticker)
class TickerAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name')
    search_fields = ('symbol', 'name')

@admin.register(StockData)
class StockDataAdmin(admin.ModelAdmin):
    list_display = ('ticker', 'date', 'close_price', 'volume')
    list_filter = ('ticker', 'date')
    search_fields = ('ticker__symbol',)
    date_hierarchy = 'date'

@admin.register(NewsArticle)
class NewsArticleAdmin(admin.ModelAdmin):
    list_display = ('headline', 'source', 'published_at')
    list_filter = ('source', 'tickers')
    search_fields = ('headline',)
    filter_horizontal = ('tickers',)