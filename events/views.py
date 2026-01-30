from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import Category, Event, Ticket, Order, OrderItem
from .forms import EventForm, TicketForm, OrderForm
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib import messages


def home(request):
    """Home page view to display featured and upcoming events"""
    featured_events = Event.objects.filter(status='published').order_by('-created')[:6]
    upcoming_events = Event.objects.filter(status='published', start_date__gt=timezone.now()).order_by('start_date')[:6]
    categories = Category.objects.all()
    
    return render(request, 'events/home.html', {
        'featured_events': featured_events,
        'upcoming_events': upcoming_events,
        'categories': categories,
    })
def register(request):
    """Simple user registration with username and password only"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

def event_list(request, category_slug=None):
    """Display list of events, optionally filtered by category"""
    category = None
    categories = Category.objects.all()
    events = Event.objects.filter(status='published')
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        events = events.filter(category=category)
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        events = events.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )
    
    # Filter by date
    filter_date = request.GET.get('date')
    if filter_date == 'today':
        today = timezone.now().date()
        events = events.filter(start_date__date=today)
    elif filter_date == 'this_week':
        today = timezone.now().date()
        end_of_week = today + timezone.timedelta(days=7)
        events = events.filter(start_date__date__range=[today, end_of_week])
    elif filter_date == 'this_month':
        today = timezone.now().date()
        events = events.filter(
            start_date__year=today.year,
            start_date__month=today.month
        )
    
    # Pagination
    paginator = Paginator(events, 9)  # 9 events per page
    page = request.GET.get('page')
    try:
        events = paginator.page(page)
    except PageNotAnInteger:
        events = paginator.page(1)
    except EmptyPage:
        events = paginator.page(paginator.num_pages)
    
    return render(request, 'events/list.html', {
        'category': category,
        'categories': categories,
        'events': events,
    })

def event_detail(request, slug):
    """Display detailed information about a specific event"""
    event = get_object_or_404(Event, slug=slug, status='published')
    tickets = Ticket.objects.filter(event=event)
    
    return render(request, 'events/detail.html', {
        'event': event,
        'tickets': tickets,
    })

@login_required
def create_event(request):
    """Create a new event"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('event_detail', slug=event.slug)
    else:
        form = EventForm()
    
    return render(request, 'events/create.html', {'form': form})

@login_required
def update_event(request, slug):
    """Update an existing event"""
    event = get_object_or_404(Event, slug=slug)
    
    # Check if the current user is the organizer
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('event_detail', slug=event.slug)
    
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('event_detail', slug=event.slug)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'events/update.html', {
        'form': form,
        'event': event
    })

@login_required
def delete_event(request, slug):
    """Delete an event"""
    event = get_object_or_404(Event, slug=slug)
    
    # Check if the current user is the organizer
    if event.organizer != request.user:
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('event_detail', slug=event.slug)
    
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('event_list')
    
    return render(request, 'events/delete.html', {'event': event})

@login_required
def purchase_ticket(request, event_slug):
    """Purchase tickets for an event without payment processing"""
    event = get_object_or_404(Event, slug=event_slug, status='published')
    
    if event.is_past:
        messages.error(request, 'This event has already ended.')
        return redirect('event_detail', slug=event.slug)
    
    if event.tickets_available <= 0:
        messages.error(request, 'Sorry, this event is sold out.')
        return redirect('event_detail', slug=event.slug)
    
    if request.method == 'POST':
        # Create new order
        order = Order.objects.create(
            user=request.user,
            total_amount=0,
            status='completed'  # Auto-complete the order
        )
        
        ticket_id = request.POST.get('ticket')
        quantity = int(request.POST.get('quantity', 1))
        
        ticket = get_object_or_404(Ticket, id=ticket_id, event=event)
        
        if quantity > event.tickets_available:
            messages.error(request, f'Only {event.tickets_available} tickets available.')
            return redirect('purchase_ticket', event_slug=event.slug)
        
        # Calculate total amount
        item_price = ticket.price * quantity
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            event=event,
            ticket=ticket,
            quantity=quantity,
            price=ticket.price
        )
        
        # Update order total
        order.total_amount = item_price
        order.save()
        
        messages.success(request, 'Tickets reserved successfully!')
        return redirect('order_confirmation', order_id=order.id)
    else:
        available_tickets = Ticket.objects.filter(event=event)
    
    return render(request, 'events/purchase.html', {
        'event': event,
        'available_tickets': available_tickets,
    })

@login_required
def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    return render(request, 'events/confirmation.html', {'order': order})

@login_required
def my_tickets(request):
    """Display user's purchased tickets"""
    orders = Order.objects.filter(user=request.user, status='completed')
    
    return render(request, 'events/my_tickets.html', {'orders': orders})

@login_required
def my_events(request):
    """Display user's created events"""
    events = Event.objects.filter(organizer=request.user)
    
    return render(request, 'events/my_events.html', {'events': events})
