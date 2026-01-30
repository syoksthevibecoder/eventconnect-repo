from django import forms
from django.utils.text import slugify
from .models import Event, Category, Ticket, Order

class EventForm(forms.ModelForm):
    """Form for creating and updating events"""
    class Meta:
        model = Event
        fields = ['title', 'category', 'description', 'location', 'venue', 
                  'start_date', 'end_date', 'image', 'max_attendees', 'status']
        widgets = {
            'start_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if start_date >= end_date:
                raise forms.ValidationError("End date must be after start date")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if not instance.slug:
            instance.slug = slugify(instance.title)
        
        if commit:
            instance.save()
        
        return instance


class TicketForm(forms.ModelForm):
    """Form for creating and updating tickets"""
    class Meta:
        model = Ticket
        fields = ['ticket_type', 'price', 'quantity']


class OrderForm(forms.Form):
    """Form for creating orders"""
    ticket = forms.ModelChoiceField(
        queryset=Ticket.objects.none(),
        widget=forms.RadioSelect,
        empty_label=None
    )
    quantity = forms.IntegerField(min_value=1, initial=1)
    
    def __init__(self, *args, **kwargs):
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)
        
        if event:
            self.fields['ticket'].queryset = Ticket.objects.filter(event=event)


class EventSearchForm(forms.Form):
    """Form for searching events"""
    query = forms.CharField(required=False, label='Search')
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label='Category'
    )
    date_filter = forms.ChoiceField(
        choices=[
            ('', 'Any time'),
            ('today', 'Today'),
            ('this_week', 'This week'),
            ('this_month', 'This month'),
        ],
        required=False,
        label='When'
    )