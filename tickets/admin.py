from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ExportActionModelAdmin

from .models import Ticket, Signature, PreventiveMaintenance, AntivirusKey, AntivirusUsage
from .resources import TicketResource


class TicketAdmin(ExportActionModelAdmin):
    resource_class = TicketResource
    list_display = ('title', 'description', 'user', 'status', 'created_at')  # Adjust as necessary


admin.site.register(Ticket)
admin.site.register(Signature)
# Register your models here.
# Customizing the admin panel titles
admin.site.site_header = _("Admin Panel")  # The text in the header
admin.site.site_title = _("Administration Panel")  # The title in the browser tab
admin.site.index_title = _("Administration Panel")
admin.site.register(PreventiveMaintenance)
@admin.register(AntivirusKey)
class AntivirusKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'used_by_count', 'suffix')

    def used_by_count(self, obj):
        """
        Display the number of unique users who have used this antivirus key.
        """
        # Count the distinct users who have used this antivirus key
        return AntivirusUsage.objects.filter(antivirus_key=obj).values('user').distinct().count()

    used_by_count.short_description = 'Number of Users'