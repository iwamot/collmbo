FROM dhi.io/python:3.14.4-debian13-dev@sha256:a8651db74106e7722b06c3f734e112a8d4e6a8130207e53e9d886c06e5ab3dd5 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.7-debian13-dev@sha256:2f0a1134997f1eaa806ceda69e3d9b92f6c6c0d035342e19271949b2c78e1aed /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:c68807a71f9271d0ff1898184a1f450c681a2f47feb5824fd6b33e70e1857ac1 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
