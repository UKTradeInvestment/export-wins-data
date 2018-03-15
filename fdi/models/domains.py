from trackstats.models import Domain, Metric

# Domains
Domain.objects.INVESTMENT = Domain.objects.register(
    ref='investment',
    name='investment'
)

# Metrics, these are associated with a domain

Metric.objects.INVESTMENT_COUNT = Metric.objects.register(
    domain=Domain.objects.INVESTMENT,
    ref='investment_count',
    name='Number of investments in the system')

Metric.objects.INVESTMENT_WON_COUNT = Metric.objects.register(
    domain=Domain.objects.INVESTMENT,
    ref='investment_won_count',
    name='Number of investments in the system at stage won')

Metric.objects.INVESTMENT_VERIFY_WIN_COUNT = Metric.objects.register(
    domain=Domain.objects.INVESTMENT,
    ref='investment_verify_win_count',
    name='Number of investments in the system at stage verify win')

Metric.objects.INVESTMENT_ACTIVE_COUNT = Metric.objects.register(
    domain=Domain.objects.INVESTMENT,
    ref='investment_active_count',
    name='Number of investments in the system at stage active')

Metric.objects.INVESTMENT_PIPELINE_COUNT = Metric.objects.register(
    domain=Domain.objects.INVESTMENT,
    ref='investment_pipeline_count',
    name='Number of investments in the system not at stage verify win or win')
