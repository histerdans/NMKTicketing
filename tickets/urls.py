from django.urls import path

from .views import ticket_create, ticket_detail, ticket_list, sign_ticket, staff_dashboard, ticket_update, \
    ticket_delete, ticket_list_partial, export_tickets, user_maintenance_history, preventive_maintenance_view, \
    maintenance_status_update, download_attachment, ict_dashboard, generate_pdf_report, ict_dashboard_staff, \
    generate_excel_report, generate_report

app_name = 'tickets'
urlpatterns = [
    path('ticket_list/', ticket_list, name='ticket_list'),
    path('ticket/new/', ticket_create, name='ticket_create'),
    path('ticket/<int:pk>/', ticket_detail, name='ticket_detail'),
    path('ticket/<int:pk>/sign/', sign_ticket, name='sign_ticket'),
    path('staff_dashboard/', staff_dashboard, name='staff_dashboard'),
    path('update/<int:pk>/', ticket_update, name='update_item_url'),
    path('delete/<int:pk>/', ticket_delete, name='delete_item_url'),
    path('tickets/partial/', ticket_list_partial, name='ticket_list_partial'),
    path('export_tickets/', export_tickets, name='export_tickets'),
    path('preventive/', preventive_maintenance_view, name='preventive'),
    path('maintenance-history/', user_maintenance_history, name='maintenance_history'),
    path('tickets/maintenance-status/', maintenance_status_update, name='maintenance_status_update'),
    path('download_attachment/<int:pk>/', download_attachment, name='download_attachment'),
    path('ict_dashboard/', ict_dashboard, name='ict_dashboard'),
    path('ict_dashboard_staff/<int:user_id>/', ict_dashboard_staff, name='staff_dashboard'),
    path('generate_report/', generate_report, name='generate_report'),
    path('generate_pdf_report/', generate_pdf_report, name='generate_pdf_report'),
    path('generate_excel_report/', generate_excel_report, name='generate_excel_report'),
]
