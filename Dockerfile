FROM python:3.11-slim-bullseye
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN mkdir /opt/app &&  \
    mkdir /opt/requirements

# Requirements
RUN pip install --upgrade pip

WORKDIR /opt/app

COPY ./requirements/ /opt/requirements/
ARG requirements
RUN pip install -r /opt/requirements/${requirements:-"pro"}.txt

# Copy code
COPY . .

CMD python -m main
