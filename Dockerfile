FROM dhi.io/python:3.14.8-debian13-dev@sha256:03cf5ae71ab5a7761ec0dcbf9d522c0209581fb5196ac303537c74d2ac92de32 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.4-debian13-dev@sha256:34076b552f25c0cd27ead5ddeb0ec82addc1ac5e8ab5d5ccf91bc6baa1528739 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:046a46512297187590b40b85e86ea2b128077d57601847ce916ecb7d919a7291 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
