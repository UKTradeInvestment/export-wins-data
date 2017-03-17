import datetime
import uuid


from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.utils import OperationalError, ProgrammingError
from django_countries.fields import CountryField

from users.models import User
from . import constants


class SoftDeleteManager(models.Manager):

    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(is_active=True)

    def inactive(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(is_active=False)

    def including_inactive(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs)


class SoftDeleteModel(models.Model):
    """ Allow inheriting models to be soft-deleted

    Intended for soft-deleting Wins and their related models, so queries on
    those models do not include soft-deleted instances by default.

    See Win model for cascading `soft_delete` and `un_soft_delete`.

    Note: shouldn't soft-delete (or un-soft-delete) any of the models which
    depend on Wins, since when Win is soft-deleted and un-soft-deleted it
    takes all it's related models with it.

    """
    class Meta:
        abstract = True
    objects = SoftDeleteManager()
    is_active = models.BooleanField(default=True)

    def soft_delete(self):
        raise Exception(
            "Should not singularly soft-delete models which depend on Win"
        )

    def un_soft_delete(self):
        raise Exception(
            "Should not singularly un-soft-delete models which depend on Win"
        )

    def delete(self, *args, **kwargs):
        if kwargs.pop('for_real', None):
            super().delete(*args, **kwargs)
        else:
            raise Exception(
                "To delete for real, pass flag `for_real`, to soft delete "
                "call `.soft_delete()`"
            )


class HVC(models.Model):

    campaign_id = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=128)

    def __str__(self):
        # note name includes code
        return self.name

    @property
    def campaign(self):
        # names are always <Name of HVC: HVCCode>
        return self.name.split(':')[0]

    @classmethod
    def choices(cls):
        try:
            return tuple([(hvc.campaign_id, hvc.name)
                         for hvc in cls.objects.all()])
        except (OperationalError, ProgrammingError):
            # small hack for when you have empty DB (e.g. running tests)
            # migrations need to initialize models
            return []


class Win(SoftDeleteModel):
    """ Information about a given "export win", submitted by an officer """

    class Meta(object):
        ordering = ['created']
        verbose_name = "Export Win"
        verbose_name_plural = "Export Wins"

    id = models.UUIDField(primary_key=True)
    user = models.ForeignKey(User, related_name="wins")
    company_name = models.CharField(
        max_length=128, verbose_name="Organisation or company name")
    cdms_reference = models.CharField(
        max_length=128, verbose_name="CDMS Reference")

    customer_name = models.CharField(
        max_length=128, verbose_name="Contact name")
    customer_job_title = models.CharField(max_length=128, verbose_name='Job title')
    customer_email_address = models.EmailField(verbose_name='Contact email')
    customer_location = models.PositiveIntegerField(
        choices=constants.UK_REGIONS,
        verbose_name="HQ location"
    )

    business_type = models.CharField(
        max_length=128,
        verbose_name="What kind of business deal was this win?",
    )
    # Formerly a catch-all, since broken out into business_type,
    # name_of_customer, name_of_export and description.
    description = models.TextField(
        verbose_name="Summarise the support provided to help achieve this win",
    )
    name_of_customer = models.CharField(
        max_length=128,
        verbose_name="Overseas customer",
    )
    name_of_export = models.CharField(
        max_length=128,
        verbose_name="What goods or services are being exported?",
    )

    type = models.PositiveIntegerField(
        choices=constants.WIN_TYPES, verbose_name="Type of win")
    date = models.DateField(verbose_name="Date business won [MM/YY]")
    country = CountryField()

    total_expected_export_value = models.BigIntegerField()
    goods_vs_services = models.PositiveIntegerField(
        choices=constants.GOODS_VS_SERVICES,
        verbose_name="Does the expected export value relate to"
    )
    total_expected_non_export_value = models.BigIntegerField()

    sector = models.PositiveIntegerField(choices=constants.SECTORS)
    is_prosperity_fund_related = models.BooleanField(
        verbose_name="Prosperity Fund", default=False)
    hvc = models.CharField(
        max_length=6,
        choices=HVC.choices(),
        verbose_name="HVC code, if applicable",
        blank=True,
        null=True,
    )
    hvo_programme = models.CharField(
        max_length=6,
        choices=constants.HVO_PROGRAMMES,
        verbose_name="HVO Programme, if applicable",
        blank=True,
        null=True
    )
    has_hvo_specialist_involvement = models.BooleanField(
        verbose_name="An HVO specialist was involved", default=False)
    is_e_exported = models.BooleanField("E-exporting programme", default=False)

    type_of_support_1 = models.PositiveIntegerField(choices=constants.TYPES_OF_SUPPORT)
    type_of_support_2 = models.PositiveIntegerField(
        choices=constants.TYPES_OF_SUPPORT, blank=True, null=True)
    type_of_support_3 = models.PositiveIntegerField(
        choices=constants.TYPES_OF_SUPPORT, blank=True, null=True)

    associated_programme_1 = models.PositiveIntegerField(
        choices=constants.PROGRAMMES, blank=True, null=True)
    associated_programme_2 = models.PositiveIntegerField(
        choices=constants.PROGRAMMES, blank=True, null=True)
    associated_programme_3 = models.PositiveIntegerField(
        choices=constants.PROGRAMMES, blank=True, null=True)

    is_personally_confirmed = models.BooleanField(
        verbose_name="I confirm that this information is complete and accurate"
    )
    is_line_manager_confirmed = models.BooleanField(
        verbose_name="My line manager has confirmed the decision to record this win"
    )

    lead_officer_name = models.CharField(
        max_length=128,
        verbose_name="Lead officer name",
        help_text="This is the name that will be included in the email to the "
                  "customer"
    )

    lead_officer_email_address = models.EmailField(
        verbose_name="Lead officer email address",
        blank=True
    )
    other_official_email_address = models.EmailField(
        verbose_name="Secondary email address",
        blank=True
    )
    line_manager_name = models.CharField(
        max_length=128, verbose_name="Line manager")
    team_type = models.CharField(max_length=128, choices=constants.TEAMS)
    hq_team = models.CharField(
        max_length=128,
        verbose_name="HQ team, Region or Post",
        choices=constants.HQ_TEAM_REGION_OR_POST
    )
    location = models.CharField(max_length=128, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, null=True)
    complete = models.BooleanField()  # has an email been sent to the customer?
    audit = models.TextField(null=True)

    def add_audit(self, text):
        """ Add text to audit field with timestamp """

        if self.audit:
            self.audit += '\n---\n'
        else:
            self.audit = ''
        self.audit += text
        self.audit += '\n' + str(datetime.datetime.utcnow())

    def __str__(self):
        return "Export win {}: {} - {}".format(
            self.pk,
            self.user,
            self.created.strftime("%Y-%m-%d %H:%M:%S"),
        )

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = str(uuid.uuid4())
        models.Model.save(self, *args, **kwargs)

    @property
    def other_officer_addresses(self):
        """ Emails of officers entered in optional fields """

        addresses = []
        if self.lead_officer_email_address:
            addresses.append(self.lead_officer_email_address)
        if self.other_official_email_address:
            addresses.append(self.other_official_email_address)
        return tuple(set(addresses))

    @property
    def target_addresses(self):
        """ Emails of officer who entered win, and other officers """

        addresses = [self.user.email]
        addresses.extend(self.other_officer_addresses)
        return tuple(set(addresses))

    @property
    def confirmed(self):
        try:
            return self.confirmation.agree_with_win
        except CustomerResponse.DoesNotExist:
            return False

    def _is_active_cascade(self, is_active):
        """ Soft-(un)delete the Win, and all objects that relate to it

        This could be done more abstractly, but KISS

        """
        self.is_active = is_active
        self.save()

        foreignkey_fields = [
            'advisors',
            'breakdowns',
            'notifications',
        ]
        for related_field in foreignkey_fields:
            related_manager = getattr(self, related_field)
            # related manager defaults to the soft-delete manager, filtering
            # out the inactive relations. but applying the .inactive method
            # drops the win filter for some reason , so have to re-apply it
            if is_active:
                qs = related_manager.inactive().filter(win=self)
            else:
                qs = related_manager.all()
            qs.update(is_active=is_active)

        # have to handle one-to-one differently
        try:
            confirmation = self.confirmation
        except ObjectDoesNotExist:
            pass
        else:
            confirmation.is_active = is_active
            confirmation.save()

    def soft_delete(self):
        self._is_active_cascade(False)

    def un_soft_delete(self):
        self._is_active_cascade(True)


class Breakdown(SoftDeleteModel):
    """ Export/non-export value broken down by given year

    Totals found in win model as `total_expected_export_value` and
    `total_expected_non_export_value`.
    """

    TYPE_EXPORT = {y: x for x, y in constants.BREAKDOWN_TYPES}['Export']

    class Meta:
        ordering = ["year"]

    win = models.ForeignKey(Win, related_name="breakdowns")
    type = models.PositiveIntegerField(choices=constants.BREAKDOWN_TYPES)
    year = models.PositiveIntegerField()
    value = models.BigIntegerField()

    def __str__(self):
        return "{}/{} {}: {}K".format(
            self.year,
            str(self.year + 1)[-2:],
            dict(constants.BREAKDOWN_TYPES)[self.type],
            self.value / 1000,
        )


class Advisor(SoftDeleteModel):
    """ Member of another team who helped with a Win """

    win = models.ForeignKey(Win, related_name="advisors")
    name = models.CharField(max_length=128)
    team_type = models.CharField(max_length=128, choices=constants.TEAMS)
    hq_team = models.CharField(
        max_length=128,
        verbose_name="HQ team, Region or Post",
        choices=constants.HQ_TEAM_REGION_OR_POST
    )
    location = models.CharField(
        max_length=128,
        verbose_name="Location (if applicable)",
        blank=True,
    )

    def __str__(self):
        return "Name: {0}, Team {1} - {2}".format(
            self.name,
            dict(constants.TEAMS)[self.team_type],
            dict(constants.HQ_TEAM_REGION_OR_POST)[self.hq_team],
        )


class CustomerResponse(SoftDeleteModel):
    """ Customer's response to being asked about a Win (aka Confirmation) """

    win = models.OneToOneField(Win, related_name="confirmation")

    our_support = models.PositiveIntegerField(
        choices=constants.RATINGS,
        verbose_name="Securing the win overall?"
    )
    access_to_contacts = models.PositiveIntegerField(
        choices=constants.RATINGS,
        verbose_name="Gaining access to contacts?"
    )
    access_to_information = models.PositiveIntegerField(
        choices=constants.RATINGS,
        verbose_name="Getting information or improved understanding of the country?"
    )
    improved_profile = models.PositiveIntegerField(
        choices=constants.RATINGS,
        verbose_name="Improving your profile or credibility in the country?"
    )
    gained_confidence = models.PositiveIntegerField(
        choices=constants.RATINGS,
        verbose_name="Having confidence to explore or expand in the country?"
    )
    developed_relationships = models.PositiveIntegerField(
        choices=constants.RATINGS,
        verbose_name="Developing or nurturing critical relationships?"
    )
    overcame_problem = models.PositiveIntegerField(
        choices=constants.RATINGS,
        verbose_name="Overcoming a problem in the country (eg legal, regulatory, commercial)?"
    )

    involved_state_enterprise = models.BooleanField(
        verbose_name="The win involved a foreign government or state-owned enterprise (eg as an intermediary or facilitator)",
        default=False
    )
    interventions_were_prerequisite = models.BooleanField(
        verbose_name="Our support was a prerequisite to generate this export value",
        default=False
    )
    support_improved_speed = models.BooleanField(
        verbose_name="Our support helped you achieve this win more quickly",
        default=False
    )
    expected_portion_without_help = models.PositiveIntegerField(
        choices=constants.WITHOUT_OUR_SUPPORT,
        verbose_name="What value do you estimate you would have achieved without our support?"
    )
    last_export = models.PositiveIntegerField(
        choices=constants.EXPERIENCE,
        verbose_name="When did your company last export goods or services?"
    )
    has_enabled_expansion_into_new_market = models.BooleanField(
        verbose_name="It enabled you to expand into a new market",
        default=False
    )
    has_enabled_expansion_into_existing_market = models.BooleanField(
        verbose_name="It enabled you to maintain or expand in an existing market",
        default=False
    )
    has_increased_exports_as_percent_of_turnover = models.BooleanField(
        verbose_name="It enabled you to increase exports as a proportion of your turnover",
        default=False
    )
    company_was_at_risk_of_not_exporting = models.BooleanField(
        verbose_name="If you hadn't achieved this win, your company might have stopped exporting",
        default=False
    )
    has_explicit_export_plans = models.BooleanField(
        verbose_name="Apart from this win, you already have specific plans to export in the next 12 months",
        default=False
    )
    # temporarily nullable for migration - should ultimately be filled in and
    # turned into a BooleanField
    agree_with_win = models.NullBooleanField(
        verbose_name="Please confirm these details are correct",
    )
    case_study_willing = models.BooleanField(
        verbose_name="Would you be willing for DIT / Exporting is GREAT to feature your success in marketing materials?"
    )

    comments = models.TextField(blank=True, verbose_name='Other comments or changes to the export details')
    name = models.CharField(max_length=256, verbose_name='Your name')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "Customer response to {}".format(self.win)


class Notification(SoftDeleteModel):
    """ Record when notifications sent (for analysis and sending followups) """

    TYPE_OFFICER = {y: x for x, y in constants.NOTIFICATION_TYPES}['Officer']
    TYPE_CUSTOMER = {y: x for x, y in constants.NOTIFICATION_TYPES}['Customer']

    win = models.ForeignKey(Win, related_name="notifications")
    user = models.ForeignKey(
        User, blank=True, null=True, related_name="notifications")
    recipient = models.EmailField()
    type = models.CharField(max_length=1, choices=constants.NOTIFICATION_TYPES)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{0} notification to {1} regarding Win {2} sent {3}".format(
            dict(constants.NOTIFICATION_TYPES)[self.type],
            self.recipient,
            self.win.id,
            self.created
        )
