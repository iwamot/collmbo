FROM dhi.io/python:3.14.4-debian13-dev@sha256:ef5e6b75134f8a02a2ebb86685a7faedd7f36ccb3832e9cbdfbbc54f25a9b5be AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.4-debian13-dev@sha256:426f12af523c26ce458a76a1d8eaac150a816bebb38922c31a88d11ddedb14f3 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:16115a2626bfdb873847b12d70180dff4bd5edf7fc1f54e60ca33668c773b547 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
