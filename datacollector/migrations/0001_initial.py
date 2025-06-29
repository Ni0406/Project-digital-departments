# Generated by Django 5.2.3 on 2025-06-24 14:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Ticker',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=10, unique=True, verbose_name='Тикер')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='Название компании')),
            ],
            options={
                'verbose_name': 'Тикер',
                'verbose_name_plural': 'Тикеры',
            },
        ),
        migrations.CreateModel(
            name='NewsArticle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('headline', models.CharField(max_length=500, verbose_name='Заголовок')),
                ('url', models.URLField(max_length=500, unique=True, verbose_name='Ссылка')),
                ('source', models.CharField(max_length=100, verbose_name='Источник')),
                ('published_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')),
                ('tickers', models.ManyToManyField(blank=True, related_name='news', to='datacollector.ticker', verbose_name='Связанные тикеры')),
            ],
            options={
                'verbose_name': 'Новостная статья',
                'verbose_name_plural': 'Новостные статьи',
                'ordering': ['-published_at'],
            },
        ),
        migrations.CreateModel(
            name='StockData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Дата')),
                ('open_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена открытия')),
                ('high_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Макс. цена')),
                ('low_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Мин. цена')),
                ('close_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена закрытия')),
                ('volume', models.BigIntegerField(verbose_name='Объем торгов')),
                ('ticker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stock_data', to='datacollector.ticker')),
            ],
            options={
                'verbose_name': 'Данные по акции',
                'verbose_name_plural': 'Данные по акциям',
                'unique_together': {('ticker', 'date')},
            },
        ),
    ]
