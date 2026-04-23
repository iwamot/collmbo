FROM dhi.io/python:3.14.4-debian13-dev@sha256:bc7f6bc5301d1b8bd0cbae374207a7e3379f812ab0744d37894cbb7a52b1579b AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.7-debian13-dev@sha256:b28ea19b1bad7175e6166a5051e8e63f6e707a5cab46f79a08da1886f4a26e0b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:e9075a8ed1e69e7573dab493947ca58bdea64409603544cd65f2d37619131165 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
