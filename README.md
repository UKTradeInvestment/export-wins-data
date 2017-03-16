The data server component for the export-wins application, a backend providing APIs.

See the corresponding projects export-wins-ui and export-wins-ui-mi and PROJECT_README.md

Note, UI project will need to be rebooted after making changes to models of this project since it gets info on startup from this project

Environment Variables you probably want to set
-----------------------------------------------

(see settings.py for details)

```
UI_SECRET='shared-ui-secret'
ADMIN_SECRET='shared-admin-secret'
MI_SECRET='shared-mi-secret'
DEBUG='1'
DATA_SERVER='localhost:8001'  # port you run this project on, for front-ends
EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
SENDING_ADDRESS='noreply@example.com'
FEEDBACK_ADDRESS='feedback@example.com'
```

## Docker

To run Postgres in a docker container run:

```bash
docker run -d -p 5432:5432 -e POSTGRES_DB=export-wins-data postgres:9
```

Now set your DATABASE_URL to include the default user `postgres`:

```bash
export DATABASE_URL='postgres://postgres@127.0.0.1:5432/export-wins-data'
```
