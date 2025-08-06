from django.contrib import admin
from .models import VerificationLog, DriverVerification

# Register your models here.
admin.site.register(VerificationLog)
admin.site.register(DriverVerification)
