from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, SenderProfile, DriverProfile, AuditLog

class DriverProfileInline(admin.StackedInline):
    model = DriverProfile
    can_delete = False
    verbose_name_plural = 'Driver Profile'

class SenderProfileInline(admin.StackedInline):
    model = SenderProfile
    can_delete = False
    verbose_name_plural = 'Sender Profile'

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'role')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('id', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'address', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    readonly_fields = ('id', 'date_joined')
    inlines = [DriverProfileInline, SenderProfileInline]

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'role', 'password1', 'password2'),
        }),
    )

admin.site.register(AuditLog)