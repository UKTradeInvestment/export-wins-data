# Export Wins

This is a very uncomplicated project, executed in a complicated way because
Security.  As such, much of this will feel like overkill to a new developer
until she realises that the requirements are such that these sorts of
precautions are necessary.

Now, with that in mind, have a look at these two architecture diagrams:

![diagrams](technical-architecture.png "Technical Architecture")


## What's Special: Alice

Basically you're looking at a simple web form split across two components: a
data server and a UI server.  The idea is that you can have `n` UI servers and
if one is compromised, the attacker can only get at `1/nth` of your traffic.

Unfortunately, Django wasn't really designed for this paradigm, so there's some
magic going on behind the scenes to make things work.  They're outlined here in
order from simplest to craziest.


## Request Signing

Thanks to [`alice.middleware.SignatureRejectionMiddleware`](https://github.com/uktrade/export-wins-data/blob/master/alice/middleware.py)
on the data server, all requests to the that server will be rejected unless
they come with a special `X-Signature: ` header.  This middleware on the data
server is where the rejection happens, and [`alice.helpers.rabbit`](https://github.com/uktrade/export-wins-ui/blob/master/alice/helpers.py)
on the UI server is where the request is signed and issued.

For the most part, there's not much to worry about here.  `rabbit` is just a
wrapper around the `requests` library, and you can treat rabbit just like
requests.  For example this code snippet:

```python
from alice.helpers import rabbit
my_response = rabbit.get("/some/data/server/path?some=argument")
```

...is the same as this:

```python
import requests
my_response = requests.get("/some/data/server/path?some=argument")
```

but using `rabbit.get()` will sign the request for you.


### If Something Goes Wrong

The rabbit class dumps stuff out into the log in the event that there's a
problem communicating with the data server.  If the server rejects your
request, or there's connectivity issues, you'll see it in the log.  In the
worst case, you should be able to tweak the code to `print(response.content)`
to see what's up.


## Session Handling and the Alice Cookie

Now that we've verified the communication between the UI server and the API
server, we can send unauthenticated requests on behalf of our users without
issue.  However, we haven't covered how we manage to identify our *users* to
the data server yet.  For this, we're doing a bit of a hack on Django's session
handling.

The diagram above should give you a good idea of how this works, but here's the
gist:

* Identity is managed *by the client* in that she is carrying around a cookie
  called (predictably) `alice`.
* This cookie is a [JSON web token](http://jwt.io/) signed by the UI server and
  containing two bits of information:
    * A session id for use in communication with the data server
    * User data the UI server can use if it wants to
* On every request to the UI, the server verifies the token and if everything
  pans out, attaches the session id and user object to `request` as `alice_id`
  and `user` respectively.
* Requests to the data server that are privileged require that the `request`
  object be passed in.  Rabbit then sets the `sessionid` cookie value to
  `request.alice_id` when it sends its request to the data server.
* The data server has no idea what's going on and assumes everything is just a
  typical Django session process.


## Where to Look

Some creative coding went into making this work.  Specifically:

* [`alice.authentication.NoCSRFSessionAuthentication`](https://github.com/uktrade/export-wins-data/blob/master/alice/authentication.py):
  There's a bigger comment in that file, but the gist is that we turn off CSRF
  protection because it's not required on a purely API box.
* [`alice.braces.LoginRequiredMixin`](https://github.com/uktrade/export-wins-ui/blob/master/alice/braces.py):
  There's absolutely nothing special about this class.  In fact, it's just a
  copy/paste of what you find in Django's class with the same name.  The only
  thing different is:
    * We stripped out anything that we're not using or don't need to override.
    * This file doesn't import anything that requires the auth stuff in the
      database (we stripped all that out since we don't need/want it).
* [`alice.middleware.AliceMiddleware`](https://github.com/uktrade/export-wins-ui/blob/master/alice/middleware.py):
  Does the aforementioned validation of the JWT coming from the client.
* [`alice.models.User`](https://github.com/uktrade/export-wins-ui/blob/master/alice/models.py):
  A fake User class, made to act like Django's standard one.  For the few cases
  where a user class is expected (like in the templates, where you do
  `{{ user.is_authenticated }}`), this will make things Just Work.


## Activity Stream

The `/activity-stream/` endpoint is protected differently, by two mechanisms:

* IP address whitelisting via the `X-Forwarded-For` header, with a comma separated list of whitelisted IPs in the environment variable `ACTIVITY_STREAM_IP_WHITELIST`.

* Hawk authentication via the `Authorization` header, with the credentials in the environment variables `ACTIVITY_STREAM_ACCESS_KEY_ID` and `ACTIVITY_STREAM_SECRET_ACCESS_KEY`.


### IP address whitelisting

The authentication blocks requests that do not have a whitelisted IP in the second-from-the-end IP in `X-Forwarded-For` header. In general, this cannot be trusted. However, in PaaS, this can be, and this is the only production environment. Ideally, this would be done at a lower level than HTTP, but this is not possible with the current architecture.

If making requests to this endpoint locally, you must manually add this header.


### Hawk authentication

In general, Hawk authentication hashing the HTTP payload and `Content-Type` header, and using a nonce, are both _optional_. Here, as with the Activity Stream endpoints in other DIT projects, both are _required_. `Content-Type` may be the empty string, and if there is no payload, then it should be treated as the empty string.


## Dynamic Form Generation (Metaclasses)

This is the craziest part of the whole thing.

Basically, you know how Django creates a form based on the declarative bits you
include in the original class definition?  Basically there's some metaclass
magic that most people never want to have to worry about that translates this:

```python
class MyForm(forms.Form):
    my_field = forms.CharField(max_length=128)
```

into this:

```python
form = MyForm()
form.fields["my_field"]  # A form field
```

The problem for this project though is that while most projects have a Django
model on which to base a form, the definition of what fields we want to have in
our form *is defined by the data server*.  Sure, we could manually recreate the
form on the UI to reflect what's defined on the API and then keep everything in
sync forever, but *who has the patience for that?*

Instead, we have two components:

* The data server has a `/schema` endpoint for every route which defines the
  fields and their properties for that route.  (For example: `/wins/` and
  `/wins/schema/`)
* The UI server has forms that inherit from
  [`alice.metaclasses.ReflectiveFormMetaclass`](https://github.com/uktrade/export-wins-ui/blob/master/alice/metaclasses.py).
  These forms are smart enough to *configure themselves based on whatever the
  data server says*

You can of course override whatever is done in this magic (just as you might
with a standard Django form, just tweak things in the `__init__()`.  In fact,
there should be some tweaking already happening in
[`wins.forms`](https://github.com/uktrade/export-wins-ui/blob/master/wins/forms.py).


### Rabbiting at Start Up

There's one caveat to this, and that's the fact that because the UI server
defines its classes based on the output of the data server, **you must start
the data server *before* the UI server**.  More importantly, if you *change*
the data server, you must restart the UI server for these changes to take
effect in your forms.


## Testing

We have *some* unit tests, but not nearly enough yet to constitute proper
coverage.  As a result, deploys and merges are still best tested in a sort of
spot-checking fashion.  Here's a method I've found to work for me:

1. Try to visit `/wins/new/` whilst not logged in.  You should be redirected to
   the login page.
2. Log in
3. Create a win
    * Include your own account for the customer email address
4. Log out
5. Use the Heroku toolkit to log into the server and make sure that the win was
   in fact created.  Note the id.
6. If the customer emails are enabled, you should have one waiting for you.  If
   they aren't, you can use the win id you got via Heroku and visit
   `/wins/review/<win_id>`
7. Fill out and submit the customer review form.

If nothing explodes, I call it a win.
