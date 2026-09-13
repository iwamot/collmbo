FROM dhi.io/python:3.14.7-debian13-dev@sha256:3b7b01e1377d7462bb50f450d795340daff1a4987c0a37ab5a94816f11c6e309 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.13-debian13-dev@sha256:8705d2524494822d15ab2ecb6d3d31acb9b43d52be8f0f5ed8e084ff2a82173b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:0a5ae8d0761b60fa18c0391f8ce32d8f0cc81f55b88b93d04267b0296ca0853c AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
