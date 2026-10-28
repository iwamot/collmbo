FROM dhi.io/python:3.14.8-debian13-dev@sha256:6e187da2b1f4075cdb7fa82a0c47f1c14e1523364ca333f0beaeb0c915c876bd AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.6-debian13-dev@sha256:ae21a2b14df7d9ea786382ca7999acba2e0a26c5fc7d23f18d7358aa9c3cc4d6 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:3b96bee5f18a1978b7093b46f9320b9f55e266339ac75d6fca5ebe0328c553c6 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
