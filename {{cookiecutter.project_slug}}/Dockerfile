# syntax=docker/dockerfile:1
FROM python:3.10-slim as base

# Setup env
ENV REPOSITORY_ROOT=/{{ cookiecutter.repository_name }}
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONFAULTHANDLER=1 PYTHONUNBUFFERED=1 PIPENV_VENV_IN_PROJECT=1 \
    PYTHONPATH=$REPOSITORY_ROOT

WORKDIR $REPOSITORY_ROOT

FROM base AS python-deps

# Install pipenv
RUN pip install pipenv

COPY ./Pipfile ./Pipfile.lock $REPOSITORY_ROOT/

# Install python dependencies in $REPOSITORY_ROOT/.venv
RUN pipenv sync

FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps $REPOSITORY_ROOT/.venv $REPOSITORY_ROOT/.venv
ENV PATH="$REPOSITORY_ROOT/.venv/bin:$PATH"

FROM runtime as app

# Install application into container
COPY ./app/ $REPOSITORY_ROOT/app/
COPY ./alembic/ $REPOSITORY_ROOT/alembic/
COPY ./alembic.ini $REPOSITORY_ROOT/

RUN useradd --system --user-group --shell /bin/false --create-home appapi; \
    chown -R appapi:appapi $REPOSITORY_ROOT

USER appapi

CMD ["python", "$REPOSITORY_ROOT/app/main.py"]
