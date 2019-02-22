import os

from django.conf import settings
from django.conf.urls import url, include
from rest_framework.routers import DefaultRouter

import csvfiles.urls
import fdi.urls
import mi.urls
import sso.oauth2_urls

from activity_stream.views import ActivityStreamViewSet
from users.views import IsLoggedIn, LoginView, LoggedInUserRetrieveViewSet, LogoutView
from wins.views import (
    WinViewSet, BreakdownViewSet, AdvisorViewSet, ConfirmationViewSet,
    LimitedWinViewSet, CSVView, DetailsWinViewSet, AddUserView,
    NewPasswordView, SendCustomerEmailView, ChangeCustomerEmailView,
    SoftDeleteWinView, SendAdminEmailView, CompleteWinsCSVView,
    CurrentFinancialYearWins
)

WINS_CSV_SECRET_PATH = os.environ.get('WINS_CSV_SECRET_PATH')

router = DefaultRouter()
router.register(r"wins", WinViewSet)
router.register(r"limited-wins", LimitedWinViewSet, base_name="limited-win")
router.register(r"details", DetailsWinViewSet, base_name="details-win")
router.register(r"confirmations", ConfirmationViewSet)
router.register(r"breakdowns", BreakdownViewSet)
router.register(r"advisors", AdvisorViewSet)

urlpatterns = [
    url(r"^", include((router.urls, 'wins'), namespace="drf")),
    url(r'^oauth2/', include((sso.oauth2_urls, 'sso'), namespace="oauth2")),
    url(r'^mi/', include((mi.urls, 'mi'), namespace="mi")),
    url(r'^mi/fdi/', include((fdi.urls, 'fdi'), namespace="fdi")),
    url(r"^csv/$", CSVView.as_view(), name="csv"),
    url(r"^csv/auto/$", CurrentFinancialYearWins.as_view(), name="csv_auto"),
    url(r"^csv/", include((csvfiles.urls, 'csv'), namespace="csv")),
    url(
        r"^admin/add-user/$",
        AddUserView.as_view(),
        name='admin-add-user',
    ),
    url(
        r"^admin/new-password/$",
        NewPasswordView.as_view(),
        name='admin-new-password',
    ),
    url(
        r"^admin/send-customer-email/$",
        SendCustomerEmailView.as_view(),
        name='admin-send-customer-email',
    ),
    url(
        r"^admin/send-admin-customer-email/$",
        SendAdminEmailView.as_view(),
        name='admin-send-admin-email',
    ),
    url(
        r"^admin/change-customer-email/$",
        ChangeCustomerEmailView.as_view(),
        name='admin-change-customer-email',
    ),
    url(
        r"^admin/soft-delete/$",
        SoftDeleteWinView.as_view(),
        name='admin-soft-delete',
    ),

    # Override DRF's default 'cause our includes brute-force protection
    url(r"^auth/login/$", LoginView.as_view(), name="login"),

    url(r"^auth/is-logged-in/$", IsLoggedIn.as_view(), name="is-logged-in"),
    url(r"^user/me/$",
        LoggedInUserRetrieveViewSet.as_view({'get': 'retrieve'}), name="user_profile"),

    url(r"^auth/logout/", LogoutView.as_view(), name="logout"),

    url(
        r'^activity-stream/$',
        ActivityStreamViewSet.as_view({'get': 'list'}),
        name='activity-stream'),

]

if settings.API_DEBUG or WINS_CSV_SECRET_PATH:
    secret_path = '/' + WINS_CSV_SECRET_PATH if WINS_CSV_SECRET_PATH else ''
    urlpatterns.append(
        url(fr"^csv{secret_path}/wins/$", CompleteWinsCSVView.as_view(), name="csv_wins"),
    )
