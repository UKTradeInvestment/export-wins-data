from django.contrib import admin

from users.models import User

USER_FIELDS = [f.name for f in User._meta.get_fields() if f.is_relation == False]


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    save_on_top = True
    actions = None
    list_display = ('id', 'name', 'email', 'is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('name', 'email')
    list_editable = ('is_staff', 'is_active', 'is_superuser')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined', 'date_modified')
    readonly_fields = USER_FIELDS
