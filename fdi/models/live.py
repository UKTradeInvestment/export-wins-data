from django.db import models

MAX_LENGTH = 255


class Investments(models.Model):
    """
    The model to query all MI data from
    """
    project_code = models.CharField(null=False, blank=False, db_index=True, max_length=MAX_LENGTH)

    stage = models.CharField(max_length=MAX_LENGTH)
    number_new_jobs = models.PositiveIntegerField(null=False, default=0)
    number_safeguarded_jobs = models.PositiveIntegerField(null=False, default=0)

    approved_high_value = models.BooleanField(default=False)
    approved_good_value = models.BooleanField(default=False)

    date_won = models.DateField()
    sector_team = models.CharField(max_length=MAX_LENGTH)
    uk_region = models.CharField(max_length=MAX_LENGTH)

    client_relationship_manager = models.CharField(max_length=MAX_LENGTH)
    company_name = models.CharField(max_length=MAX_LENGTH)
    company_reference = models.CharField(max_length=MAX_LENGTH)

    investment_value = models.PositiveIntegerField(default=0)
    foreign_equity_investment = models.PositiveIntegerField(default=0)