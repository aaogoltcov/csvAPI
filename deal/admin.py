from django.contrib import admin
from deal.models import Deal


@admin.register(Deal)
class DealsAdmin(admin.ModelAdmin):
    pass
