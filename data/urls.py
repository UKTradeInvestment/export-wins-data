import os
from django.conf import settings
from django.conf.urls import url, include

from rest_framework.routers import DefaultRouter

from users.views import IsLoggedIn, LoginView, UserRetrieveViewSet

from wins.views import (
    WinViewSet, BreakdownViewSet, AdvisorViewSet, ConfirmationViewSet,
    LimitedWinViewSet, CSVView, DetailsWinViewSet, AddUserView,
    NewPasswordView, SendCustomerEmailView, ChangeCustomerEmailView,
    SoftDeleteWinView, SendAdminEmailView, CompleteWinsCSVView
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
    url(r"^", include(router.urls, namespace="drf")),
    url(r'^saml2/', include('sso.saml2_urls', namespace="saml2")),
    url(r'^oauth2/', include('sso.oauth2_urls', namespace="oauth2")),
    url(r'^mi/', include('mi.urls', namespace="mi", app_name="mi")),
    url(r'^mi/fdi/', include('fdi.urls', namespace="fdi", app_name="fdi")),
    url(r"^csv/$", CSVView.as_view(), name="csv"),
    url(r"^csv/", include('csvfiles.urls', namespace="csv", app_name="csv")),
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
        UserRetrieveViewSet.as_view({'get': 'retrieve'}), name="user_profile"),

    url(r"^auth/", include('rest_framework.urls', namespace="rest_framework")),

]

if settings.API_DEBUG or WINS_CSV_SECRET_PATH:
    secret_path = '/' + WINS_CSV_SECRET_PATH if WINS_CSV_SECRET_PATH else ''
    urlpatterns.append(
        url(fr"^csv{secret_path}/wins/$", CompleteWinsCSVView.as_view(), name="csv_wins"),
    )
