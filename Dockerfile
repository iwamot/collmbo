FROM dhi.io/python:3.14.7-debian13-dev@sha256:ac8cea62b21ca63ecfde5a9398c8fbcf4db72bd3d96fc72e7618e1561d0551d9 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.5-debian13-dev@sha256:11db0690d61981bd53784d1d1c3cc763510c8f5c699fdbf7f9fa9446f1705f69 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:4fe7c5d1dbeacefbf9c5e85146b63e9cf5511e8b361a77430a8511889fbd26e9 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
