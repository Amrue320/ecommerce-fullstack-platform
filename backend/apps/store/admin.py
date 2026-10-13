from django.contrib import admin
from .models import Profile, Category, Product, CartItem, Order, OrderItem
admin.site.register(Profile)
admin.site.register(Category)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name","category","price","stock","is_active")
    search_fields = ("name","description")
    list_filter = ("category","is_active")
admin.site.register(CartItem)
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id","user","total","status","created_at")
    list_filter = ("status","created_at")
    inlines = [OrderItemInline]
