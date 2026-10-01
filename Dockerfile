FROM dhi.io/python:3.14.7-debian13-dev@sha256:8ca22a7569e6152307c766622994e0e0e0115c99f7c6583a73aa6f2cac022281 AS builder
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
