import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render, redirect

from accounts.models import Feedback
from tickets.models import Ticket
from .forms import ContactForm


def cover_page(request):
    template = "index.html"
    # Get distinct categories from the Ticket model
    categories = Ticket.objects.values_list('title', flat=True).distinct()

    # Initialize an empty dictionary for the counts
    data = {
        'categories': list(categories),
        'closed_counts': [],
        'followup_counts': [],
        'total_counts': [],
        'open_counts': []
    }

    # Fetch counts for each category
    for category in data['categories']:
        data['closed_counts'].append(Ticket.objects.filter(status='Closed', title=category).count())
        data['followup_counts'].append(Ticket.objects.filter(status='Closed', title=category, follow_up=True).count())
        data['total_counts'].append(Ticket.objects.filter(title=category).count())
        data['open_counts'].append(Ticket.objects.filter(status='Open', title=category).count())

    # Prepare the context for rendering
    context = {
        'data': data
    }

    return render(request, template, context)


def feedback_create(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)  # Create form instance with POST data
        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            messages.success(request, 'Feedback Sent successfully!')
            print('Feedback Sent successfully!')
            return redirect('cover_page')
    else:
        form = ContactForm()  # Create an empty form instance for GET requests
    objs = (Feedback.objects.all())

    context = {'form': form,
               'feedbacks': objs, }
    return render(request, 'index.html', context)





@login_required
def delete_ticket(request, pk):
    ticket = Ticket.objects.get(pk=pk)
    if request.method == 'POST':
        ticket.delete()
        logger.info(f'Ticket {ticket.id} deleted', extra={'username': request.user.username})
        # Redirect or render response as needed


def ticket_summary_view(request):
    # Example queries to count tickets (adjust as needed for your model fields and logic)
    closed_tickets_by_category = Ticket.objects.filter(status='closed').count()
    closed_tickets_with_follow_up = Ticket.objects.filter(status='closed', follow_up=True).count()
    total_tickets_raised = Ticket.objects.all().count()
    total_tickets_open = Ticket.objects.filter(status='open').count()

    context = {
        'closed_tickets_by_category': closed_tickets_by_category,
        'closed_tickets_with_follow_up': closed_tickets_with_follow_up,
        'total_tickets_raised': total_tickets_raised,
        'total_tickets_open': total_tickets_open,
    }

    return render(request, 'index.html', context)
