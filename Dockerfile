FROM dhi.io/python:3.14.10-debian13-dev@sha256:1c5d6bb037de4b40aba4b1ef0b1e9c8d2f0bae59a2fd1f2b4e46ea9de03ae206 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.7-debian13-dev@sha256:25fb9e920eeff3140c667d0fcc92c28b6d22e57772a7a28af9b8827734edaded /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:c98bac9272579c507b971989a7b9ea4f2b883ef2842bf2ff00a7b79b9d948a0e AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
