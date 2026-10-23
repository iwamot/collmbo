FROM dhi.io/python:3.14.8-debian13-dev@sha256:03cf5ae71ab5a7761ec0dcbf9d522c0209581fb5196ac303537c74d2ac92de32 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.4-debian13-dev@sha256:a5d1bbced387e66cd2f14d8df93cc3a2216c472a848a0380b4b1e9d346566e94 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:36c38f4be040b095f67fbb0982d18875518f1b58d23b9ad3cc8bc903a7f7524e AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
