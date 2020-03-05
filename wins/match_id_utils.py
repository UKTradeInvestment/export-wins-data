from data.settings import COMPANY_MS_URL, COMPANY_MS_HAWK_KEY_ID, COMPANY_MS_HAWK_KEY_SECRET
from mohawk import Sender
import requests
import json


def get_company_house_or_cdms_number(ref):
    """Validate the data to return a company house or cdms number."""
    if ref is None or len(ref) == 0:
        return {}
    try:
        if len(ref) == 8:
            """
                Attempt to convert the company house number to an int, we"re not going to use the value
                because we do not want to make any assumptions for the format we only care if all the chracters are
                numbers and are 8 digits long. e.g if a number is 000123 the int will return 123.
            """
            int(ref)
            return {"companies_house_id": ref}
        return {"cdms_ref": ref}
    except ValueError:
        return {"cdms_ref": ref}


def get_company_win_json(wins):
    """Get win in a json format for the company matching service."""
    descriptions = []
    for win in wins:
        descriptions.append({
            "id": str(win.pk),
            "company_name": win.company_name,
            "contact_email": win.customer_email_address,
            **get_company_house_or_cdms_number(win.cdms_reference),
        })
    return json.dumps({
        "descriptions": descriptions,
    })


def request_match_ids(wins):
    """Make a request to the company matching service and return the response."""
    content = get_company_win_json(wins)
    sender = Sender({
        "id": COMPANY_MS_HAWK_KEY_ID,
        "key": COMPANY_MS_HAWK_KEY_SECRET,
        "algorithm": "sha256"},
        url=COMPANY_MS_URL,
        method="POST",
        content_type="application/json",
        content=content,
    )

    return requests.post(COMPANY_MS_URL, data=content, headers={
        "Authorization": sender.request_header,
        "Content-Type": "application/json",
    })
