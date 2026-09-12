FROM dhi.io/python:3.14.7-debian13-dev@sha256:3b7b01e1377d7462bb50f450d795340daff1a4987c0a37ab5a94816f11c6e309 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.13-debian13-dev@sha256:fd0ea15c37175765b90f7af121fac49405f58ba109fc0de3c7183e23406eb0aa /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:b7f0db069020910078cdd92f26326ec4b07c3d746e865b1a8aaf16a22b62e55e AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
