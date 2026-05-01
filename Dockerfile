FROM dhi.io/python:3.14.4-debian13-dev@sha256:6d08fa284915b06d2fcc0405c0732871a6b95973174e43ceed16c4452a1233d5 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.8-debian13-dev@sha256:7836090fee6a7af9e14db5747eda9ad16b1886da3771f4677e9ee160e7722d54 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:8e43543853920751ccb13b7f7ce39cf6fb7c9f8192a644a74f368e1e71ef6ae8 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
