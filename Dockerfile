FROM dhi.io/python:3.14.3-debian13-dev@sha256:1ac10ee926e3e57c6cdf564e0afccd19388d8afb1166087e8d7837a11c29b162 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.12@sha256:72ab0aeb448090480ccabb99fb5f52b0dc3c71923bffb5e2e26517a1c27b7fec /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:129b2dd5cd4b93e5b47beedcf9363b0700be1f5228c40879283e920c52441980 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
