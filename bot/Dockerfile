FROM python:3.10 as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes






FROM python:3.10

WORKDIR /w24ok-bot-bot

COPY --from=requirements-stage /tmp/requirements.txt /w24ok-bot-bot/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /w24ok-bot-bot/requirements.txt

COPY ./ .

ENTRYPOINT [ "python3", "Bot.py"]
