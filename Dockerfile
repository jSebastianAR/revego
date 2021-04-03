FROM python:3.7-alpine

WORKDIR /app/
COPY ./pumps/ /app/
COPY requeriments.txt /app/
RUN apk update
RUN apk add libxml2-dev libxslt-dev postgresql-dev gcc python3-dev musl-dev python-dev build-essential zlib1g-dev libxslt1-dev libffi-dev libssl-dev
RUN pip install --no-cache-dir -r requeriments.txt

CMD [ "python", "/pumps/manage.py", "runserver", "0.0.0.0:8080"]