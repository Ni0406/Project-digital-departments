# datacollector/models.py

from django.db import models

class Ticker(models.Model):
    """Модель для хранения тикеров компаний."""
    symbol = models.CharField(max_length=10, unique=True, verbose_name="Тикер")
    name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Название компании")

    def __str__(self):
        return self.symbol

    class Meta:
        verbose_name = "Тикер"
        verbose_name_plural = "Тикеры"


class StockData(models.Model):
    """Модель для хранения исторических данных по ценам акций."""
    ticker = models.ForeignKey(Ticker, on_delete=models.CASCADE, related_name='stock_data')
    date = models.DateField(verbose_name="Дата")
    open_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена открытия")
    high_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Макс. цена")
    low_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Мин. цена")
    close_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена закрытия")
    volume = models.BigIntegerField(verbose_name="Объем торгов")

    def __str__(self):
        return f"{self.ticker.symbol} on {self.date}"

    class Meta:
        verbose_name = "Данные по акции"
        verbose_name_plural = "Данные по акциям"
        # Уникальность для пары тикер-дата, чтобы не было дубликатов
        unique_together = ('ticker', 'date')


class NewsArticle(models.Model):
    """Модель для хранения финансовых новостей."""
    headline = models.CharField(max_length=500, verbose_name="Заголовок")
    url = models.URLField(max_length=500, unique=True, verbose_name="Ссылка")
    source = models.CharField(max_length=100, verbose_name="Источник")
    published_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")
    tickers = models.ManyToManyField(Ticker, blank=True, related_name='news', verbose_name="Связанные тикеры")

    def __str__(self):
        return self.headline

    class Meta:
        verbose_name = "Новостная статья"
        verbose_name_plural = "Новостные статьи"
        ordering = ['-published_at']