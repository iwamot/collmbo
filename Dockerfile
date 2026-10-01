FROM dhi.io/python:3.14.7-debian13-dev@sha256:17360e42c456dc161e0429e2ba1039cf40cd64ea81d033b9e6190263adc1ae22 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.20-debian13-dev@sha256:078e378aff66dfd7dad1287a96342155359f2ba4681c76b1faec2c21fc1db1e5 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:21b78d6daf1b6ba5e1a96c07de143364fc1a7da65eeda24c7ecfc3328646f6e6 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
