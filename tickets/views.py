import io

import pandas as pd
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, FileResponse, Http404
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa

from accounts.models import User
from .forms import TicketForm, SignatureForm, PreventiveMaintenanceForm
from .models import Signature, PreventiveMaintenance, Ticket, AntivirusKey, AntivirusUsage

from django.shortcuts import render
from django.db.models import Count
from datetime import datetime


@login_required(login_url='accounts:login')
def ticket_list(request):
    if request.user.is_staff:
        tickets = Ticket.objects.all().order_by('-status', '-created_at')
    else:
        tickets = Ticket.objects.filter(user=request.user).order_by('-status', '-created_at')
    return render(request, 'ticket_list.html', {'tickets': tickets})


def ticket_list_partial(request):
    if request.user.is_staff:
        tickets = Ticket.objects.all().order_by('-status', '-created_at')
    else:
        tickets = Ticket.objects.filter(user=request.user).order_by('-status', '-created_at')
    return render(request, 'tickets_table.html', {'tickets': tickets})


@login_required(login_url='accounts:login')
def ticket_create(request):
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
            messages.success(request, 'Ticket raised successfully!')
            return redirect('tickets:ticket_list')
        else:
            messages.error(request, 'Ticket creation unsuccessful. Please try again.')
    else:
        form = TicketForm()
    return render(request, 'create_ticket.html', {'form': form})


# View to download the attachment (restricted to admin and staff)
@login_required
@user_passes_test(lambda u: u.is_staff or u.is_admin)
def download_attachment(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if ticket.attachment:
        response = FileResponse(ticket.attachment.open(), as_attachment=True)
        return response
    else:
        return HttpResponseForbidden("No attachment available.")


@login_required(login_url='accounts:login')
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    signature = Signature.objects.filter(ticket=ticket).first()
    return render(request, 'ticket_detail.html', {'ticket': ticket, 'signature': signature})


@login_required(login_url='accounts:login')
def sign_ticket(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)

    # Get or create the Signature object for the ticket
    signature, created = Signature.objects.get_or_create(ticket=ticket)

    if request.method == 'POST':
        form = SignatureForm(request.POST, instance=signature)

        if form.is_valid():
            form.save()
            ticket.status = 'closed'  # Set the ticket status to closed
            # Update the resolution date, notes, and follow-up status
            ticket.resolution_notes = form.cleaned_data['remarks']  # Assuming remarks is in the form
            ticket.resolution_date = timezone.now()  # Set current date and time
            ticket.follow_up = form.cleaned_data.get('follow_up')  # Check if follow-up is needed
            # Update the 'doneby' field to the current user (technician)
            ticket.doneby = request.user.employee_name  # Store the username or use request.user if you want the User object
            ticket.save()

            # Update the maintenance status if linked
            preventive_maintenance = PreventiveMaintenance.objects.filter(ticket_id=ticket.id).first()
            if preventive_maintenance:
                # Update the status of the preventive maintenance record to 'Activated'
                preventive_maintenance.status = 'Activated'
                preventive_maintenance.followup = form.cleaned_data.get(
                    'follow_up')  # Update followup status in PreventiveMaintenance
                preventive_maintenance.save()

            # Set follow-up status in Signature model
            signature.follow_up = form.cleaned_data.get('follow_up')
            signature.technician = request.user  # Set the current user as the technician
            signature.technician_signature = request.POST.get(
                'technician_signature')  # Get the technician's signature from the form
            signature.save()

            messages.success(request, 'Ticket closed successfully!')
            return redirect('tickets:ticket_list')
        else:
            messages.error(request, 'Both signatures are required to close the ticket. Please try again.')
    else:
        form = SignatureForm(instance=signature)

    return render(request, 'sign_ticket.html', {'ticket': ticket, 'form': form})


@login_required(login_url='accounts:login')
def staff_dashboard(request):
    open_tickets = Ticket.objects.filter(status='open')
    closed_tickets = Ticket.objects.filter(status='closed')
    return render(request, 'staff_dashboard.html', {
        'open_tickets': open_tickets,
        'closed_tickets': closed_tickets
    })


def ticket_update(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method == 'POST':
        form = TicketForm(request.POST, instance=ticket)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            messages.success(request, 'Ticket updated successfully!')
            return redirect('tickets:ticket_list')
    else:
        form = TicketForm(instance=ticket)
    return render(request, 'tickets_update.html', {'form': form, 'tickets': ticket, })


@login_required(login_url='accounts:login')
def ticket_delete(request, pk):
    """Handles deleting a reminder."""
    reminder = Ticket.objects.get(pk=pk)
    reminder.delete()
    messages.success(request, 'Ticket deleted successfully!')
    return redirect('tickets:ticket_list')


@login_required(login_url='accounts:login')
def export_tickets(request):
    # Query the necessary data
    tickets = Ticket.objects.all().select_related('user')

    # Prepare data for open and closed tickets
    closed_tickets_data = []
    open_tickets_data = []

    for ticket in tickets:
        signature = None
        technical_name = 'Not Signed'
        remarks = 'No Remarks'
        signed_at = None

        # Check if signature exists
        if hasattr(ticket, 'signature'):
            signature = ticket.signature
            technical_name = signature.technician.employee_name if signature.technician else 'Not Signed'
            remarks = signature.remarks if signature.remarks else 'No Remarks'
            signed_at = signature.signed_at if ticket.status == 'Closed' else None

        # Ensure datetimes are timezone-naive
        created_at = ticket.created_at

        # Convert timezone-aware datetimes to timezone-naive if necessary
        if timezone.is_aware(created_at):
            created_at = timezone.localtime(created_at).replace(tzinfo=None)
            signed_at = timezone.localtime(signed_at).replace(tzinfo=None)

        # Prepare the ticket data
        ticket_data = {
            'Employee Department': ticket.user.department,
            'Employee Name': ticket.user.employee_name,
            'Technical Name': technical_name,
            'Ticket Title': ticket.title,
            'Description': ticket.description,
            'Remarks': remarks,
            'When Created': created_at,
            'When Closed': signed_at,  # Will be None for open tickets
        }

        # Add to appropriate list based on status
        if ticket.status == 'Closed':
            closed_tickets_data.append(ticket_data)
        else:  # Open tickets
            # Remove fields with None values from open tickets
            filtered_open_ticket_data = {k: v for k, v in ticket_data.items() if v is not None}
            open_tickets_data.append(filtered_open_ticket_data)

    # Create DataFrames
    closed_tickets_df = pd.DataFrame(closed_tickets_data)
    open_tickets_df = pd.DataFrame(open_tickets_data)

    # Order by 'When Closed' (signed_at) for closed tickets
    if not closed_tickets_df.empty:
        closed_tickets_df.sort_values(by='When Closed', inplace=True)

    # Order by 'When Opened' for open tickets
    if not open_tickets_df.empty:
        open_tickets_df.sort_values(by='When Created', inplace=True)

    # Set up response for Excel file
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="tickets_{current_time}.xlsx"'

    # Write data to separate sheets in the Excel file
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        if not closed_tickets_df.empty:
            closed_tickets_df.to_excel(writer, index=False, sheet_name='Closed Tickets')
        if not open_tickets_df.empty:
            open_tickets_df.to_excel(writer, index=False, sheet_name='Open Tickets')

    return response


def maintenance_status_update(request):
    # Fetch the maintenance history for the logged-in user
    history = PreventiveMaintenance.objects.filter(
        user=request.user
    ).select_related('ticket').values(
        'card_id', 'status', 'department', 'machine_type', 'computer_name', 'ticket__doneby'  # Get doneby from Ticket
    )

    return JsonResponse(list(history), safe=False)


@login_required(login_url='accounts:login')
def preventive_maintenance_view(request):
    user = request.user  # Get the logged-in user

    # Filter antivirus keys to only show those available for the current user
    available_keys = AntivirusKey.objects.filter(
        id__in=[key.id for key in AntivirusKey.objects.all() if key.available_for_user(user)]
    )

    # Initialize the form with the available keys
    form = PreventiveMaintenanceForm(request.POST or None, user=user)
    form.fields['antivirus_key'].queryset = available_keys

    if request.method == 'POST':
        user = request.user  # Get the logged-in user
        # Filter antivirus keys to only show those available for the current user
        available_keys = AntivirusKey.objects.filter(
            id__in=[key.id for key in AntivirusKey.objects.all() if key.available_for_user(user)]
        )

        form = PreventiveMaintenanceForm(request.POST or None, user=request.user)
        form.fields['antivirus_key'].queryset = available_keys
        if form.is_valid():
            # Get the validated antivirus key
            antivirus_key = form.cleaned_data['antivirus_key']

            # Check if the user has already used this antivirus key
            if AntivirusUsage.objects.filter(user=request.user, antivirus_key=antivirus_key).exists():
                form.add_error('antivirus_key', 'You have already used this antivirus key.')
            else:
                # Create a new usage entry
                AntivirusUsage.objects.create(user=request.user, antivirus_key=antivirus_key)

                # Create the ticket first
                ticket = Ticket(
                    title='Preventive Maintenance',
                    description='Request for preventive maintenance',
                    user=user
                )
                ticket.save()  # Save the ticket to get a ticket number

                # Create preventive maintenance instance
                preventive_instance = form.save(commit=False)
                preventive_instance.user = user  # Link the logged-in user
                preventive_instance.department = getattr(user, 'department', None)  # Set department from user
                preventive_instance.antivirus_key = antivirus_key  # Link the antivirus key
                preventive_instance.ticket = ticket  # Link the ticket

                # Now save the preventive maintenance instance
                preventive_instance.save()

                # Update the preventive maintenance record with the generated ticket number
                preventive_instance.card_id = ticket.ticket_number  # Assign the ticket number to the preventive instance
                preventive_instance.save()  # Save the instance again with the updated ticket number

                # Check if the logged-in user is staff (ICT staff) to sign and close the ticket
                if request.user.is_staff:
                    preventive_instance.doneby = request.user.username  # Set the doneby field to the ICT staff username
                    preventive_instance.status = 'Activated'  # Update status to 'Activated'
                    ticket.status = 'Closed'  # Close the ticket
                    ticket.save()

                    preventive_instance.save()  # Save the instance again with updated status and doneby

                messages.success(request, "Maintenance record and ticket created successfully.")
                return redirect('tickets:maintenance_history')  # Redirect after saving
        else:
            form = PreventiveMaintenanceForm(user=user)  # Reinitialize the form on error

    return render(request, 'preventive.html', {'form': form})


@login_required(login_url='accounts:login')
def user_maintenance_history(request):
    # Fetch the maintenance history for the logged-in user
    history = PreventiveMaintenance.objects.filter(user=request.user).select_related('ticket')

    return render(request, 'maintenance_history.html', {'history': history})


@login_required(login_url='accounts:login')
def ict_dashboard(request):
    # Count closed tickets
    closed_tickets = Ticket.objects.filter(status='closed').count()

    # Calculate category percentages
    total_tickets = Ticket.objects.count()
    category_counts = (
        Ticket.objects.values('title')
        .annotate(count=Count('title'))
        .order_by('-count')
    )

    category_percentages = [
        {
            'category': item['title'],
            'percentage': (item['count'] / total_tickets) * 100 if total_tickets else 0
        }
        for item in category_counts
    ]

    context = {
        'closed_tickets': closed_tickets,
        'category_percentages': category_percentages,
        'current_month': 'October',  # Example, adjust as needed
    }
    return render(request, 'ict_dashboard.html', context)


@login_required(login_url='accounts:login')
def ict_dashboard_staff(request, user_id):
    if not request.user.is_staff:
        return redirect('home')  # Redirect if the user is not a staff member

    closed_tickets = Ticket.objects.filter(doneby=request.user.employee_name, status='closed').count()

    # Calculate ticket categories
    category_data = Ticket.objects.filter(doneby=request.user.employee_name, status='closed').values('title').annotate(
        total=Count('id'))

    # Prepare data for the pie chart
    category_percentages = []
    total_tickets = sum(item['total'] for item in category_data)

    for item in category_data:
        category_percentages.append({
            'category': item['title'],
            'percentage': (item['total'] / total_tickets * 100) if total_tickets > 0 else 0
        })

    current_year = timezone.now().year  # Assuming you want the current year for the modal
    context = {
        'closed_tickets': closed_tickets,
        'category_percentages': category_percentages,
        'current_year': current_year,
    }

    return render(request, 'ict_dashboard_staff.html', context)


def generate_report(request):
    # Get month and year from GET parameters
    month = int(request.GET.get('month'))
    year = int(request.GET.get('year'))

    # Filter tickets based on the closed (or resolution) date's month and year
    tickets = Ticket.objects.filter(
        status='closed',
        updated_at__month=month,
        updated_at__year=year
    )

    # Check if any tickets are available for the selected criteria
    if not tickets.exists():
        return HttpResponse("No report available for the selected month and year.", content_type="text/plain")

    # Prepare the context data for rendering the PDF
    context = {
        'tickets': tickets,
        'selected_month': month,
        'selected_year': year,
    }

    # Render the PDF template as an HTML string
    html_string = render_to_string('pdf_report.html', context)

    # Create a bytes buffer to hold the PDF data
    pdf_buffer = io.BytesIO()

    # Generate the PDF
    pdf_status = pisa.CreatePDF(io.BytesIO(html_string.encode("UTF-8")), dest=pdf_buffer)

    # Check if there was an error in PDF generation
    if pdf_status.err:
        return HttpResponse("Error generating PDF", content_type="text/plain")

    # Set the response content
    pdf_buffer.seek(0)
    response = HttpResponse(pdf_buffer, content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="tickets_report_{month}_{year}.pdf"'
    return response


@login_required(login_url='accounts:login')
def generate_pdf_report(request, ):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        month = int(request.GET.get('month'))
        year = int(request.GET.get('year'))

        # Ensure current user is a staff member
        if not request.user.is_staff:
            messages.error(request, "Access denied: Only staff members can view this dashboard.")
            return redirect('home')

        current_user = get_object_or_404(User, id=user_id)
        employee_name = current_user.employee_name

        # Filter tickets based on the closed date's month and year
        tickets = Ticket.objects.filter(
            status='closed',
            doneby=employee_name,
            updated_at__month=month,
            updated_at__year=year
        )

        # Check if any tickets are available for the selected criteria
        if not tickets.exists():
            return HttpResponse("No report available for the selected month and year.", content_type="text/plain")

        # Prepare the context data for rendering the PDF
        context = {
            'tickets': tickets,
            'selected_month': month,
            'selected_year': year,
        }

        # Render the PDF template as an HTML string
        html_string = render_to_string('pdf_report_staff.html', context)

        # Create a bytes buffer to hold the PDF data
        pdf_buffer = io.BytesIO()

        # Generate the PDF
        pdf_status = pisa.CreatePDF(io.BytesIO(html_string.encode("UTF-8")), dest=pdf_buffer)

        # Check if there was an error in PDF generation
        if pdf_status.err:
            return HttpResponse("Error generating PDF", content_type="text/plain")

        # Set the response content
        pdf_buffer.seek(0)
        response = HttpResponse(pdf_buffer, content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="tickets_report_{month}_{year}.pdf"'
        return response


@login_required(login_url='accounts:login')
def generate_excel_report(request):
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
        month = int(request.GET.get('month'))
        year = int(request.GET.get('year'))

        # Ensure current user is a staff member
        if not request.user.is_staff:
            messages.error(request, "Access denied: Only staff members can view this dashboard.")
            return redirect('home')

        current_user = get_object_or_404(User, id=user_id)
        employee_name = current_user.employee_name

        # Filter tickets based on the closed date's month and year
        tickets = Ticket.objects.filter(
            status='closed',
            doneby=employee_name,
            updated_at__month=month,
            updated_at__year=year
        )

        # Check if any tickets are available for the selected criteria
        if not tickets.exists():
            return HttpResponse("No report available for the selected month and year.", content_type="text/plain")

        # Prepare data for Excel
        data = []
        for ticket in tickets:
            data.append({
                'Ticket Number': ticket.ticket_number,
                'Title': ticket.title,
                'Description': ticket.description,
                'Closed By': ticket.doneby,
                'Resolution Date': ticket.updated_at.strftime('%Y-%m-%d'),
            })

        # Create a DataFrame and then export to Excel
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="tickets_report_{month}_{year}.xlsx"'

        # Write the DataFrame to the response
        df.to_excel(response, index=False)

        return response
