from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path('', views.home, name='home'),
    
    # Event listing pages
    path('events/', views.event_list, name='event_list'),
    path('events/category/<slug:category_slug>/', views.event_list, name='events_by_category'),
    
    # Event CRUD operations
    path('events/<slug:slug>/', views.event_detail, name='event_detail'),
    path('events/create/', views.create_event, name='create_event'),
    path('events/<slug:slug>/update/', views.update_event, name='update_event'),
    path('events/<slug:slug>/delete/', views.delete_event, name='delete_event'),
    
    # Ticket purchase and order management
    path('events/<slug:event_slug>/purchase/', views.purchase_ticket, name='purchase_ticket'),
    path('orders/<int:order_id>/confirmation/', views.order_confirmation, name='order_confirmation'),
    
    # User dashboard
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('my-events/', views.my_events, name='my_events'),

    path('register/', views.register, name='register'),
]