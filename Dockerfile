FROM python:3.7.5-slim-buster
LABEL maintainer="Nick Janetakis <nick.janetakis@gmail.com>"

RUN apt-get update && apt-get install -qq -y \
  build-essential libpq-dev --no-install-recommends

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .
RUN pip install --editable .

CMD gunicorn -c "python:config.gunicorn" "turboquant.app:create_app()"
