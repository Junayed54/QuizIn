from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.utils.translation import gettext_lazy as _

class CustomUserAdmin(UserAdmin):
    # Define fields to be used in displaying the User model
    fieldsets = (
        (None, {'fields': ('msisdn', 'password')}),
        (_('Personal info'), {'fields': ('username', 'email', 'role')}),  # Added role here
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )

    # Define fields for the 'add user' form in the admin panel
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('msisdn', 'password1', 'password2', 'role'),  # Added role here
        }),
    )

    # Fields to display in the user list view in the admin panel
    list_display = ('msisdn', 'username', 'email', 'role', 'is_staff', 'is_active')  # Added role here
    search_fields = ('msisdn', 'username', 'email')
    ordering = ('msisdn',)

# Register the custom user model with the admin panel
admin.site.register(CustomUser, CustomUserAdmin)
