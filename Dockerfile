FROM python:3.8-buster as builder

WORKDIR /app/
ENV PYTHONPATH=/app

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry config virtualenvs.in-project false

COPY pyproject.toml poetry.lock* /app/
RUN poetry install

ONBUILD COPY . /
