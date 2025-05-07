from import_export import resources
from import_export.fields import Field
from import_export.widgets import DateTimeWidget
from .models import Ticket, Signature


class TicketResource(resources.ModelResource):
    employee_name = Field(column_name='Employee Name', attribute='user__employee_name')
    department = Field(column_name='Employee Department', attribute='user__department')
    technical_name = Field(column_name='Technical Name',
                           attribute='ticket_signature__technician_signature')  # Assuming a technical name is stored in Signature model
    title = Field(column_name='Ticket Title', attribute='title')
    description = Field(column_name='Description', attribute='description')
    created_at = Field(column_name='When Created', attribute='created_at', widget=DateTimeWidget())
    updated_at = Field(column_name='When Updated', attribute='updated_at',
                       widget=DateTimeWidget())  # Ensure this field exists
    closed_at = Field(column_name='When Closed', attribute='closed_at',
                      widget=DateTimeWidget())  # Ensure this field exists
    opened_at = Field(column_name='When Opened', attribute='opened_at',
                      widget=DateTimeWidget())  # Ensure this field exists
    remarks = Field(column_name='Remarks', attribute='ticket_signature__remarks')

    class Meta:
        model = Ticket
        fields = ('employee_name', 'department', 'technical_name', 'title', 'description', 'created_at', 'updated_at',
                  'closed_at', 'opened_at', 'remarks')

    def get_export_queryset(self):
        # Modify this method if you need to filter the queryset before exporting
        return super().get_export_queryset()
