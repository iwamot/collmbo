FROM dhi.io/python:3.14.7-debian13-dev@sha256:3fe8324735434c3471b243d23e16de4893d3ad67e8baa093a3a87c5d75ab1ccf AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.13-debian13-dev@sha256:8705d2524494822d15ab2ecb6d3d31acb9b43d52be8f0f5ed8e084ff2a82173b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:5e1e7ddf4efddd05e414390978128730799d4150738c75060364228a073741ec AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
