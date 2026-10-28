FROM dhi.io/python:3.15.2-debian13-dev@sha256:0286e67c40c516e235b0417136c76bd746be9ed5ff267e3c32bf3e1c63525bb8 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.6-debian13-dev@sha256:ae21a2b14df7d9ea786382ca7999acba2e0a26c5fc7d23f18d7358aa9c3cc4d6 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.15.2-debian13@sha256:dff2966bc273ff38fae6f84d21180d3265864611b4f805e44695449f11343d72 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
