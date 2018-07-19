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
DATA_SECRET='shared-data-secret'
DEBUG='1'
DATA_SERVER='localhost:8001'  # port you run this project on, for front-ends
EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend'
SENDING_ADDRESS='noreply@example.com'
FEEDBACK_ADDRESS='feedback@example.com'
```

## Dependencies

### Database
You need a Postgres database to connect to, to run Postgres in a docker container run:

```bash
docker run -d -p 5432:5432 -e POSTGRES_DB=export-wins-data postgres:9
```

Now set your DATABASE_URL to include the default user `postgres`:

```bash
export DATABASE_URL='postgres://postgres@127.0.0.1:5432/export-wins-data'
```
#### Dummy data

Once you have a database you'll need some data.

##### Start with the migrate command to set-up your tables:

```bash
$ ./manage.py migrate
```

This means you have some MI targets and all the wins tables set up but no users or wins

##### Create a user:

```bash
$ ./manage.py create_mi_user --email foo@bar.com
User foo@bar.com created with password: ********
User foo@bar.com added to mi_group
```

##### Create missing HVCs:

```bash
$ ./manage.py create_missing_hvcs
```

##### Create some wins:

the following command will create 1000 confirmed wins across all sectors as the last
user that was added to the system

```bash
$ ./manage.py generate_fake_db 1000
```

This currently only creates wins for FY2015/2016 so you'll need to view that year if
you want to see any data.

## Docker

The image for this should be built by docker hub automatically.

Ensuring you have the required env variables as mentioned above, start the docker container:

```bash
docker run --name ew-data -d -p 8000:8000 -e "DEBUG=True" -e "DATA_SECRET=${DATA_SECRET}" -e "API_DEBUG=True" -e "SECRET_KEY=${SECRET_KEY}" -e "ADMIN_SECRET=${ADMIN_SECRET}" -e "UI_SECRET=${UI_SECRET}" -e "MI_SECRET=${MI_SECRET}" -e "DATABASE_URL=${DATABASE_URL}" -e "EMAIL_BACKEND=${EMAIL_BACKEND}" -e "AWS_KEY_CSV_READ_ONLY_ACCESS=${AWS_KEY_CSV_READ_ONLY_ACCESS}" -e "AWS_SECRET_CSV_READ_ONLY_ACCESS=${AWS_SECRET_CSV_READ_ONLY_ACCESS}" -e "AWS_REGION_CSV=${AWS_REGION_CSV}" ukti/export-wins-data:latest
```

To stop the container run:

```bash
docker stop ew-data
```

### OSX

If you want to run this app and a database in docker, there is a little trick that needs to done. As the network integration for OSX is not as nice as Linux, you will need to create an alias to enable the app container to talk to the database container.

Run this in terminal:

```bash
'[[ `ifconfig -r lo0 | grep 10.200.10.1 | wc -l` -eq 0 ]] && sudo ifconfig lo0 alias 10.200.10.1/24'
```

It will check whether the alias exists and if not it will prompt for the sudo password and create it.

There were some issues with the 'django.core.mail.backends.console.EmailBackend' so I setup [maildev](https://github.com/djfarrelly/MailDev) instead.
```bash
docker run -d -p 1080:80 -p 1025:25 djfarrelly/maildev
```
This allows you to see the emails that are being sent by the system as it acts as a mail server and has a web interface for a fake inbox to show the emails - just set the EMAIL_HOST and EMAIL_PORT to that of maildev.

Ensuring you have the required env variables as mentioned above, start the docker container:

```bash
docker run --name ew-data -d -p 8000:8000 -e "DEBUG=True" -e "DATA_SECRET=${DATA_SECRET}" -e "API_DEBUG=True" -e "SECRET_KEY=${SECRET_KEY}" -e "ADMIN_SECRET=${ADMIN_SECRET}" -e "UI_SECRET=${UI_SECRET}" -e "MI_SECRET=${MI_SECRET}" -e "DATABASE_URL=postgres://postgres@10.200.10.1:5432/export-wins-data" -e "EMAIL_HOST=${EMAIL_HOST}" -e "EMAIL_PORT=${EMAIL_PORT}" -e "AWS_KEY_CSV_READ_ONLY_ACCESS=${AWS_KEY_CSV_READ_ONLY_ACCESS}" -e "AWS_SECRET_CSV_READ_ONLY_ACCESS=${AWS_SECRET_CSV_READ_ONLY_ACCESS}" -e "AWS_REGION_CSV=${AWS_REGION_CSV}" ukti/export-wins-data:latest
```
