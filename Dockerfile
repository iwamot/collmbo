FROM dhi.io/python:3.14.10-debian13-dev@sha256:8a87f4a0df5f310a87d04c2c9e6169689b0b0ddfd5ce5518d29d7c55c3cda8bc AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.9-debian13-dev@sha256:c9b0c17d4efe26a98bcbd8597c202a4c7f76774aa479ba42f5f327322c42a547 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:b0c1a2f69276c576f8cf1e4ffe3d2c2e6cf3d0592525611b77aebdf1ed55f958 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
