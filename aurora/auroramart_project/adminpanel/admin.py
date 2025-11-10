from django.contrib import admin
from .models import Banner, Customer, Product, Order, OrderItem, DecisionTreeModel, Chat, Message

# Register your models here.

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title',)
    ordering = ('order', '-created_at')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'age', 'gender')
    search_fields = ('email', 'name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'category', 'price', 'quantity_on_hand', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('sku', 'name')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'placed_at', 'total_amount', 'fulfillment_status')
    list_filter = ('fulfillment_status', 'placed_at')
    search_fields = ('customer__email',)

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'subject', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer__email', 'subject')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'sender_name', 'is_from_customer', 'created_at')
    list_filter = ('is_from_customer', 'created_at')

