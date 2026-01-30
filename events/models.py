from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.db.models import Sum

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ('name',)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('events_by_category', args=[self.slug])


class Event(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='events')
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events_organized')
    description = models.TextField()
    location = models.CharField(max_length=255)
    venue = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    image = models.ImageField(upload_to='events/%Y/%m/%d/', blank=True)
    max_attendees = models.PositiveIntegerField(default=100)
    
    class Meta:
        ordering = ('-start_date',)
        indexes = [
            models.Index(fields=['-start_date']),
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('event_detail', args=[self.slug])
    
    @property
    def is_past(self):
        return self.end_date < timezone.now()
    
    @property
    def tickets_sold(self):
        total = self.orders.filter(order__status='completed').aggregate(Sum('quantity'))
        return total['quantity__sum'] or 0
    
    
    
    @property
    def tickets_available(self):
        return self.max_attendees - self.tickets_sold


class Ticket(models.Model):
    TICKET_TYPES = (
        ('regular', 'Regular'),
        ('vip', 'VIP'),
        ('early_bird', 'Early Bird'),
    )
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='tickets')
    ticket_type = models.CharField(max_length=20, choices=TICKET_TYPES, default='regular')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.get_ticket_type_display()} ticket for {self.event.title}"


class Order(models.Model):
    ORDER_STATUS = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=ORDER_STATUS, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        ordering = ('-created',)
    
    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='orders')
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity} {self.ticket.get_ticket_type_display()} tickets for {self.event.title}"
    
    # Add this property
    @property
    def total_price(self):
        return self.price * self.quantity