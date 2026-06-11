FROM python:3.14-slim AS builder

ENV VIRTUAL_ENV=/opt/venv

RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .


FROM python:3.14-slim

WORKDIR /app

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY --from=builder $VIRTUAL_ENV $VIRTUAL_ENV

COPY ./src/ /app
COPY docker-entrypoint.sh /usr/local/bin/

ENV PYTHONPATH=/app

CMD ["python", "-m", "healthchecker.main"]
