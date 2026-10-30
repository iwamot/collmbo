FROM dhi.io/python:3.14.8-debian13-dev@sha256:d596be714808bdbaff280777fb66bd0d018c07a60b2f04558960900690ddb438 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.6-debian13-dev@sha256:d6d83d18e96a6ed138a3bfe270d1aba33ad4af5acbfb0f4815a77d92f6477cb6 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:c68dbc34dede320c455aa75855ac0eedd5e26d0063faf1dcf0e237183487c0a3 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
