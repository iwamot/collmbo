FROM dhi.io/python:3.14.5-debian13-dev@sha256:b727f60de61d57ead918909bf8c0f4a10174fc622921764b9cbd0ca65eaba867 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.19-debian13-dev@sha256:a5a2aca09637cf08ac2ec5758f389c45465c9816bd9beb45e5a2eb5f082b275b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.5-debian13@sha256:71518e0b8aec16aac480a8c392c43f0b77a2cffd71160b09912657a60ee7fe49 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
