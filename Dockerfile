FROM python:3.8

RUN apt-get update && apt-get install -y postgresql-client xmlsec1

RUN mkdir /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY alice /app/alice
COPY data /app/data
COPY gunicorn /app/gunicorn
COPY mi /app/mi
COPY users /app/users
COPY wins /app/wins
COPY fixturedb /app/fixturedb
COPY sso /app/sso
COPY core /app/core
COPY fdi /app/fdi
COPY csvfiles /app/csvfiles
COPY activity_stream /app/activity_stream
COPY datasets /app/datasets

COPY manage.py /app/manage.py
COPY start.sh /app/start.sh
COPY start-wait-for-db.sh /app/start-wait-for-db.sh

WORKDIR /app

EXPOSE 8000
CMD ./start.sh
