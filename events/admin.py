from django.contrib import admin
from .models import Category, Event, Ticket, Order, OrderItem

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'start_date', 'end_date', 'status', 'tickets_sold', 'tickets_available']
    list_filter = ['status', 'category', 'start_date']
    search_fields = ['title', 'description', 'location']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'
    inlines = [TicketInline]
    readonly_fields = ['created', 'updated']
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'organizer', 'description')
        }),
        ('Event Details', {
            'fields': ('location', 'venue', 'start_date', 'end_date', 'image', 'max_attendees')
        }),
        ('Status', {
            'fields': ('status', 'created', 'updated')
        }),
    )


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['event', 'ticket_type', 'price', 'quantity']
    list_filter = ['ticket_type', 'event']
    search_fields = ['event__title']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['event', 'ticket']
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created', 'status', 'total_amount']
    list_filter = ['status', 'created']
    search_fields = ['user__username', 'user__email']
    inlines = [OrderItemInline]
    date_hierarchy = 'created'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'event', 'ticket', 'quantity', 'price']
    list_filter = ['order__status']
    search_fields = ['event__title', 'order__user__username']