FROM dhi.io/python:3.14.7-debian13-dev@sha256:fb4a72388838d755e534dd3e08df599b30ef210327d970aafd08e8dc37b19aca AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.8-debian13-dev@sha256:cee85cafd2f7766b60c61cfa80f9c433c9b9697beb5f0345fead6d1e88374644 /uv /usr/local/bin/uv
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
