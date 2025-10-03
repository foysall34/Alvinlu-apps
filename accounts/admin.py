from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User , UserProfile


class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'full_name', 'role', 'is_staff', 'is_active', 'last_login')

    search_fields = ('email', 'full_name')

    ordering = ('email',)
    

    list_filter = ('role', 'is_staff', 'is_active', 'groups')

   
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
    
            'fields': ('email', 'full_name', 'role', 'password',),
        }),
    )


    filter_horizontal = ('groups', 'user_permissions')

admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)