from django.contrib import admin
from django.db import transaction
from django.db.models import Sum

from wins.constants import BREAKDOWN_TYPES
from wins.models import Advisor, Breakdown, CustomerResponse, DeletedWin, Win

ALL_WIN_FIELDS = [f.name for f in Win._meta.get_fields() if f.is_relation == False]

BREAKDOWN_TYPE_TO_NAME = {
    'Outward Direct Investment': 'odi',
    'Export': 'export',
    'Non-export': 'non_export',
}


class BaseTabularInline(admin.TabularInline):
    extra = 0
    can_delete = False
    exclude = ('is_active',)


class BreakdownInline(BaseTabularInline):
    model = Breakdown

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('type', 'year')


class AdvisorInline(BaseTabularInline):
    model = Advisor
    verbose_name_plural = 'Contributing Advisors'


class BaseStackedInline(admin.StackedInline):
    classes = ('grp-collapse grp-open',)
    inline_classes = ('grp-collapse grp-open',)
    extra = 0
    can_delete = False
    exclude = ('is_active',)


class CustomerResponseInline(BaseStackedInline):
    model = CustomerResponse

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Win)
class WinAdmin(admin.ModelAdmin):
    actions = ('soft_delete',)
    list_display = (
        'id', 'user', 'company_name', 'customer_name', 'customer_location', 'country', 'sector',
        'date', 'created')
    search_fields = ('id', 'company_name', 'customer_name')
    list_editable = ()
    list_filter = (
        'user', 'company_name', 'customer_name', 'customer_location', 'country', 'sector',
        'date', 'created')
    exclude = ['is_active']
    readonly_fields = (
        'id',
        'user',
        'created',
        'updated',
        'total_expected_export_value',
        'total_expected_non_export_value',
        'total_expected_odi_value',
    )
    fieldsets = (
        ('Overview', {'fields': (
            'id', 'user', 'company_name', 'customer_name', 'created', 'updated', 'audit',
            'total_expected_export_value', 'total_expected_non_export_value',
            'total_expected_odi_value',
        )}),
        ('Win details', {'fields': (
            'country', 'date', 'description', 'name_of_customer', 'goods_vs_services',
            'name_of_export', 'sector', 'hvc')}),
        ('Customer details', {'fields': (
            'cdms_reference', 'customer_email_address', 'customer_job_title', 'customer_location',
            'business_potential', 'export_experience')}),
        ('DIT Officers', {'fields': (
            'lead_officer_name', 'team_type', 'hq_team', 'line_manager_name',
            'lead_officer_email_address', 'other_official_email_address')}),
        ('DIT Support', {'fields': (
            'type_of_support_1', 'type_of_support_2', 'type_of_support_3', 'associated_programme_1',
            'associated_programme_2', 'associated_programme_3', 'associated_programme_4',
            'associated_programme_5')}),
    )

    inlines = (BreakdownInline, CustomerResponseInline, AdvisorInline)

    @staticmethod
    def _update_win_totals(win):
        with transaction.atomic():
            breakdowns = win.breakdowns.select_for_update(of=('win_ptr'))
            for bid, bn in BREAKDOWN_TYPES:
                setattr(win, f'total_expected_{BREAKDOWN_TYPE_TO_NAME[bn]}_value',
                        breakdowns.filter(type=bid).aggregate(sum=Sum('value'))['sum'] or 0)
            win.save()

    def save_related(self, request, form, formsets, change):
        super(WinAdmin, self).save_related(request, form, formsets, change)
        self._update_win_totals(formsets[0].queryset[0].win)

    def soft_delete(self, request, queryset):
        for r in queryset.all():
            r.soft_delete()

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DeletedWin)
class DeletedWinAdmin(WinAdmin):
    readonly_fields = ALL_WIN_FIELDS + ['user']
    inlines = tuple()
    actions = ('undelete',)

    def undelete(self, request, queryset):
        for r in queryset.all():
            r.un_soft_delete()

    def get_queryset(self, request):
        return self.model.objects.inactive()

    def has_change_permission(self, request, obj=None):
        return False
