FROM dhi.io/python:3.14.10-debian13-dev@sha256:03f8d94bd764161d264de69e1e179154ade93f19ad8bed97ee67549cd99aa4a4 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.7-debian13-dev@sha256:2585792a493eef2a76aa2910cdf62a99c3c8e9a60aabb95724357d9bfe3f3b90 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:b9a406607492644a1ef9809af4be9c6527fce6b644a5bef94ef4275dd1705126 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
