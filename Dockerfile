FROM dhi.io/python:3.14.6-debian13-dev@sha256:d6ad3867fa18f944fc339c67081ed5a0767f4b854283b6c2a60d4afb2bb4d1bd AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.28-debian13-dev@sha256:0fcb62029662c42f6444690bd4a1c7aac35d5b797cbff02806a0f127c8efce47 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:bf1b4520f335d2d4921757cf4c0d7589a00ff303a741eb3c2af9f4bdc5ac44fc AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
