FROM python:3.14-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
COPY lib/ ./lib/

RUN uv sync

COPY services/log-listener/ ./app

EXPOSE 9020

CMD ["uv", "run", "-m", "app.main"]
