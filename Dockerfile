FROM dhi.io/python:3.14.5-debian13-dev@sha256:d8917bb8ab38b3e474a222142f4f07b54ebc5e69ace9cf957acc5f258b00c8c3 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.17-debian13-dev@sha256:d47efbfb994c4db8bf7e8e9f88085045549fa9d5dd4daf6ce0a03946315ce286 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.5-debian13@sha256:4c20a9a5ea50f6cbce78dc399e535462df723e05d805e81bea68e626f44706ec AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
