FROM dhi.io/python:3.14.3-debian13-dev@sha256:5e79fe77bdf98210f443d4a79fc87ad2c4da3e7047432752ba0a38094ac3b6fa AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.11.0@sha256:e49fde5daf002023f0a2e2643861ce9ca8a8da5b73d0e6db83ef82ff99969baf /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:e9a0e8e8462ff6d260b761648199226ccdbbb9fbbe55e354264f871fb25fa270 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
