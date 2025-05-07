from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _
from .models import User, Feedback

admin.site.register(User)
admin.site.register(Feedback)
# Customizing the admin panel titles
admin.site.site_header = _("NMKTechAssist Administration Panel")  # The text in the header
admin.site.site_title = _("NMKTechAssist Administration Panel")  # The title in the browser tab
admin.site.index_title = _("Welcome to NMKTechAssist Administration Panel")

# Remove Group Model from admin. We're not using it.
admin.site.unregister(Group)
