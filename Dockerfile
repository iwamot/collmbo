FROM dhi.io/python:3.14.7-debian13-dev@sha256:f1e8ebcc3ba8d0dc43885ed2852d9b80159044a8d2e3baf0b30c4c726de37c55 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.10-debian13-dev@sha256:9c2e241e7c3602c9c5be0baf889975063cc49ac5488db7b4306eae701cdd7789 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:f965b2c477d44c80c2cc6763a9d42617889dcfb5b94b5b4d5e8e38751155322f AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
