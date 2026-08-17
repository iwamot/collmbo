FROM dhi.io/python:3.14.7-debian13-dev@sha256:35263a6c329e601a836a011a27792d3ae84f387b9055b40035b0649d5ce68e3c AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.5-debian13-dev@sha256:f929aff2aa851d5b09aae84ee33efa804801d31661da07847cc8c025f7b5b910 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:0536ccad57c9be08128bd2a6f0982570086ec943a88033f4f53f7adffe407903 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
