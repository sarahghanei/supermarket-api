from django.contrib import admin
from market.models import Product, OrderRow, Order, Customer

# Register your models here.
admin.site.register(Customer)
admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderRow)
