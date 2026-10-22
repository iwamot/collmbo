FROM dhi.io/python:3.14.8-debian13-dev@sha256:03cf5ae71ab5a7761ec0dcbf9d522c0209581fb5196ac303537c74d2ac92de32 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.4-debian13-dev@sha256:a5d1bbced387e66cd2f14d8df93cc3a2216c472a848a0380b4b1e9d346566e94 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:046a46512297187590b40b85e86ea2b128077d57601847ce916ecb7d919a7291 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
