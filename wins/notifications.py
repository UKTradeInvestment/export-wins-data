from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def generate_officer_email(win):
    body = render_to_string("wins/email/officer-thanks.email", {
        "win": win,
        "feedback_address": settings.FEEDBACK_ADDRESS
    })

    return {
        'subject': "Thank you for submitting a new Export Win.",
        'body': body,
        'from': settings.SENDING_ADDRESS,
    }


def send_other_officers_email(win):
    """ Send mail to other officers notifying them customer has been sent link
    to customer response form

    """

    email_dict = generate_officer_email(win)
    email_dict['to'] = win.other_officer_addresses
    if not email_dict['to']:
        return

    send_mail(
        email_dict['subject'],
        email_dict['body'],
        email_dict['from'],
        email_dict['to'],
    )


def generate_customer_email(url, win):

    body = render_to_string("wins/email/customer-notification.email", {
        "win": win,
        "url": url
    })
    html_body = render_to_string("wins/email/customer-notification.html", {
        "win": win,
        "url": url
    })

    subject = "Please confirm {} helped with your export success".format(
        win.lead_officer_name,
    )

    return {

        'subject': subject,
        'body': body,
        'html_body': html_body,
        'from': settings.FEEDBACK_ADDRESS,
        'to': (win.customer_email_address,),
    }


def send_customer_email(win):
    """ Send mail to customer asking them to confirm a win """

    url = 'https://www.exportwins.service.trade.gov.uk/wins/review/' + str(win.pk)
    email_dict = generate_customer_email(url, win)
    send_mail(
        email_dict['subject'],
        email_dict['body'],
        email_dict['from'],
        email_dict['to'],
        html_message=email_dict['html_body'],
    )


def send_officer_notification_of_customer_response(customer_response):
    """ Email win officer(s) to let them know customer has responded """

    subject = "Customer response to Export Win"
    body = render_to_string(
        "wins/email/officer-confirmation.email",
        {
            "customer_response": customer_response,
            "feedback_address": settings.FEEDBACK_ADDRESS,
        },
    )
    send_mail(
        subject,
        body,
        settings.SENDING_ADDRESS,
        customer_response.win.target_addresses,
    )
