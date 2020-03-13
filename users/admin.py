from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    actions = ('deactivate',)
    list_display = (
        'name', 'id', 'email', 'is_staff', 'is_active', 'is_superuser', 'date_joined', 'last_login', 'sso_user_id')
    search_fields = ('name', 'email', 'sso_user_id')
    list_editable = ('is_staff', 'is_active', 'is_superuser')
    list_filter = (
        'is_staff', 'is_active', 'is_superuser', 'date_joined', 'date_modified', 'last_login')

    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
