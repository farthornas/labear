# This Dockerfile is based on the artile: 
# https://medium.com/@albertazzir/blazing-fast-python-docker-builds-with-poetry-a78a66f5aed0
# Python build image
FROM python:3.12-bookworm as builder

RUN  apt-get update &&  pip install poetry==1.7.1 



ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Set the working directory inside the container
WORKDIR /app

COPY pyproject.toml poetry.lock ./
RUN touch README.md

#RUN poetry install --without dev --sync --no-root && rm -rf $POETRY_CACHE_DIR
RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root \
    && poetry run pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu \
    && poetry run pip3 install speechbrain
    

# Python runtime image
FROM python:3.12-slim-bookworm as runtime

RUN pip install poetry==1.7.1 && apt-get update && apt-get install ffmpeg libavcodec-extra -y

    COPY pyproject.toml poetry.lock ./

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY labear_api ./labear_api

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "labear_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
