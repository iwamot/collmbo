FROM dhi.io/python:3.14.3-debian13-dev@sha256:783ea51e030d54eedb9a5d6d181e855f6cab227dc5a43c620fe10bdda151bc30 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.8@sha256:88234bc9e09c2b2f6d176a3daf411419eb0370d450a08129257410de9cfafd2a /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:f4d1867af73a7cd51a5705d4a8d433ed810e55c2f6a22f3296ca5c45e02e4337 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
