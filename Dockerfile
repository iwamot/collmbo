FROM dhi.io/python:3.14.10-debian13-dev@sha256:d213b825a7e3514111e8738ba47e7365919802a40f84f34822b2b182cd58fe98 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.6-debian13-dev@sha256:a64074ff9d8b5982c783290b70c7c20b0801e2614fa6b1c9d809c277c489e763 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:f2b6c1fc00a73758f90e2d93aa2924e88cb162ff153156670a7aa67cc97f1733 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
