#Python baseimage
FROM python:3.12

RUN pip install poetry==1.7.1


ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 

# Set the working directory inside the container
WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY labear_api ./labear_api

RUN touch README.md

RUN poetry install  


EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "labear_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
