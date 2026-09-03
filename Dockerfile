FROM dhi.io/python:3.14.7-debian13-dev@sha256:fb4a72388838d755e534dd3e08df599b30ef210327d970aafd08e8dc37b19aca AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.9-debian13-dev@sha256:4ef6a4f3127b8a9d4097407381c2f3c7270f428e1bd1bc4355263e362b347dd7 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:acd4a6acf99b3bfa3ff8c8d06f5232296f6e59bcac03e7ed4ba54ac8ffa41f0f AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
