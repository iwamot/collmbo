FROM dhi.io/python:3.14.10-debian13-dev@sha256:405f74fad5143e4aedbcadf79acd7662f4613088beea3d3a08f103e478b96ade AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.10-debian13-dev@sha256:79d5364d32a28d7191ece4185199e10f88cf3b31a82ad34ff73a806955ae9f7f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:b0c1a2f69276c576f8cf1e4ffe3d2c2e6cf3d0592525611b77aebdf1ed55f958 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
