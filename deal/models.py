from django.db import models


class Deal(models.Model):
    customer = models.CharField(max_length=36, verbose_name='Логин покупателя')
    item = models.CharField(max_length=36, verbose_name='Наименование товара')
    total = models.FloatField(verbose_name='Сумма сделки')
    quantity = models.IntegerField(verbose_name='Количество товара, шт.')
    date = models.DateTimeField(auto_now=False, verbose_name='Дата и время регистрации сделки')

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = "Список продуктов"
        ordering = ('-date',)

    def __str__(self):
        return "%s %s %s" % (self.customer, self.item, self.date)
