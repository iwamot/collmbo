FROM dhi.io/python:3.14.7-debian13-dev@sha256:712dbf7a20932c614106e3914483fa48a2e0cd9a84c6d20e036cb40fdc1172db AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.17-debian13-dev@sha256:f23ef2e05ec486dbac214f2bb7f2816cf7bae63df54a209029f04bc88aaf92ea /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:98e331175ee3c13b8005ccc64ead5c71be975ebfa2bb254fbd03124f6550c26c AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
