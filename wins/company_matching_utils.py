import json
from urllib.parse import urljoin

from mohawk import Sender
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout


class CompanyMatchingServiceException(Exception):
    """
    Base exception class for Company matching service related errors.
    """


class CompanyMatchingServiceHTTPError(Exception):
    """
    Base exception class for Company matching service related errors.
    """


class CompanyMatchingServiceTimeoutError(CompanyMatchingServiceException):
    """
    Exception for when a timeout was encountered when connecting to Company matching service.
    """


class CompanyMatchingServiceConnectionError(CompanyMatchingServiceException):
    """
    Exception for when an error was encountered when connecting to Company matching service.
    """


def _post(path, json_body):
    """
    Sends a HAWK authenticated post request to the company matching service
    with a json body.
    """
    url = urljoin(settings.COMPANY_MATCHING_SERVICE_BASE_URL, path)
    # Signs a request
    sender = Sender(
        {
            'id': settings.COMPANY_MATCHING_HAWK_ID,
            'key': settings.COMPANY_MATCHING_HAWK_KEY,
            'algorithm': 'sha256'
        },
        url=url,
        method='POST',
        content_type='application/json',
        content=json.dumps(json_body),
    )
    # Post JSON to the company matching service
    response = requests.post(
        url,
        json=json_body,
        headers={
            'Authorization': sender.request_header,
            'Content-Type': 'application/json',
        }
    )
    response.raise_for_status()
    if response.ok:
        # Verify response from the company matching service
        sender.accept_response(
            response.headers['Server-Authorization'],
            content=response.content,
            content_type=response.headers['Content-Type'],
        )
    return response


def _request_match_companies(json_body):
    """
    Queries the company matching service with the given json_body. E.g.:
    {
        "descriptions": [
            {
                "id": "1",
                "companies_house_id": "0921309",
                "duns_number": "d210"
                "company_name":"apple",
                "contact_email": "john@apple.com",
                "cdms_ref": "782934",
                "postcode": "SW129RP"
            }
        ]
    }

    Note that the ID field typically the company UUID that is returned by the api for data mapping.
    ID and at least one of the following fields companies_house_id, duns_number, company_name,
    contact_email, cdms_ref and postcode are required.
    """
    if not all([
        settings.COMPANY_MATCHING_SERVICE_BASE_URL,
        settings.COMPANY_MATCHING_HAWK_ID,
        settings.COMPANY_MATCHING_HAWK_KEY,
    ]):
        raise ImproperlyConfigured('The all COMPANY_MATCHING_SERVICE_* setting must be set')

    response = _post('api/v1/company/match/', json_body)
    return response


def _company_house_or_cdms_number(ref):
    """Validate the data to return a company house or cdms number."""
    if bool(ref):
        if len(ref) == 8:
            """
            Attempt to convert the company house number to an int, we're not going to use the value
            because we do not want to make any assumptions for the format we only care if all the chracters are
            numbers and are 8 digits long. e.g if a number is 000123 the int will return 123.
            """
            try:
                int(ref)
                return {'companies_house_id': ref}
            except ValueError:
                pass
        return {'cdms_ref': ref}
    else:
        return {}


def _format_company_for_post(wins):
    """Format the Company model to json for the POST body."""
    return {
        'descriptions': [
            {
                'id': str(win.pk),
                'company_name': win.company_name,
                'contact_email': win.customer_email_address,
                **_company_house_or_cdms_number(win.cdms_reference),
            } for win in wins
        ],
    }


def update_match_ids(wins):
    """
    Get companies match from a Win queryset and updates the match_id fields from the company matching service.
    Raises exception an requests.exceptions.HTTPError for status, timeout and a connection error.
    """
    try:
        response = _request_match_companies(_format_company_for_post(wins))
    except ConnectionError as exc:
        error_message = 'Encountered an error connecting to Company matching service'
        raise CompanyMatchingServiceConnectionError(error_message) from exc
    except Timeout as exc:
        error_message = 'Encountered a timeout interacting with Company matching service'
        raise CompanyMatchingServiceTimeoutError(error_message) from exc
    except HTTPError as exc:
        error_message = (
            'The Company matching service returned an error status: '
            f'{exc.response.status_code}'
        )
        raise CompanyMatchingServiceHTTPError(error_message) from exc
    return response
