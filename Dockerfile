FROM dhi.io/python:3.14.7-debian13-dev@sha256:f1e8ebcc3ba8d0dc43885ed2852d9b80159044a8d2e3baf0b30c4c726de37c55 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.9-debian13-dev@sha256:4ef6a4f3127b8a9d4097407381c2f3c7270f428e1bd1bc4355263e362b347dd7 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:9062bae24604a79f5233ce8fa70095dbc3033ac073ef6db23ae1019668fc1fa1 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
