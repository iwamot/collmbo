FROM dhi.io/python:3.14.6-debian13-dev@sha256:5acf54c5ce21277f52115d45e217915779f8ce43a3667ea0b37a642bc7b7c8a7 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.2-debian13-dev@sha256:26fb6ff59d1534d7aaa93f2c377f7a6c44e3842044208a9a033577b6f5985214 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:ddeb1bbca979bcd099bc4dfda0c238b21a8b7df10f7240ae97788818c27e8fd7 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
