FROM dhi.io/python:3.14.7-debian13-dev@sha256:908651cc7c24caa59e552b21687fcd02ebded18b2ffc151c13ca6712739ba594 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.17-debian13-dev@sha256:f23ef2e05ec486dbac214f2bb7f2816cf7bae63df54a209029f04bc88aaf92ea /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:7a5510681f1ece5a31b1f1540d3c9c3cc61b4503befe4394280b8602fcd0ff55 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
