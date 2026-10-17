FROM dhi.io/python:3.14.8-debian13-dev@sha256:df0b3685c0d843d3d978c74b50f5fb7b55640d1fe24e90cb9ab4c5212307616d AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.0-debian13-dev@sha256:f9231579f059aa7889d333b6ff7720f5751d275a4de13fb8587884a9ea51e7b9 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:b2dee88be07689a608f86c392dd863f20399f8ffcbe99eff6bdb4f04485d9298 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
