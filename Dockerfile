FROM dhi.io/python:3.14.8-debian13-dev@sha256:d37bda175781350c2238b776baa8ece7589d4c5eb026ea883489dcb8e4948dd6 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.22-debian13-dev@sha256:051d45fa34a3c6ec2ff5424931199c0de74db075cd439dcb9eaa0a9d054bc8f0 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:2af3a6573fdecaaeb5c5a8073ced2d511cafa38b4b1205ee8d4ab820b866bd20 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
