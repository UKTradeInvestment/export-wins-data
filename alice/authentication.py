from rest_framework.authentication import SessionAuthentication


class NoCSRFSessionAuthentication(SessionAuthentication):
    """
    Django REST Framework ships with three authentication systems:

    * Basic Auth requires that each request include the username & password. As
      this would require the UI to retain this information, that's not
      happening.
    * Token Auth is what we were using at first, but it's effectively a bearer
      token system, with static tokens that don't even change after logout.
    * Session Auth exists so that DRF can be used as part of a website to
      handle ajax requests etc.  It's also used by the Browseable API.

    Given these three options, the only palatable choice is Session Auth,
    however because of its typical use case, *it enforces CSRF* which is a pain
    in the ass for our architecture (the UI is handling CSRF issues, so the
    data server doesn't have to).

    The fix therefore was to use our own authentication that extends
    SessionAuthentication and simply skips the CSRF enforcement.  The only
    other reasonable alternative that I could see is to basically implement
    Oauth2 on both the UI and the data server -- not something I'm keen on for
    such a small project.  Once this is rolled into data-hub, the auth
    component will be thrown out anyway.
    """

    def enforce_csrf(self, request):
        pass
