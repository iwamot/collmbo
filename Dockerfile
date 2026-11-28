FROM dhi.io/python:3.14.10-debian13-dev@sha256:6dd1bbf9e7e5cdbaf75f0d10c73c7ec68967225054a42b75b6ab7a14f4b19318 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.10-debian13-dev@sha256:2086e09c885c7dafb1f7dd98df25383b46dbd9cdda90a8b32ecd9cf0410e1056 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:282989a5124554f3c890ac318aed419d047243b78ab57fca8ea376fbd9b7c1b2 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
