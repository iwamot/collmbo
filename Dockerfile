FROM dhi.io/python:3.14.4-debian13-dev@sha256:1f6554d34550a8f3a62a36aab197d266111798018af18bcc852128a970f2cc5b AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.7-debian13-dev@sha256:b28ea19b1bad7175e6166a5051e8e63f6e707a5cab46f79a08da1886f4a26e0b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:eca8d67bc52bcae66bb74a924708ef58b866f229ae3b1e79c2bd24cb2f4c304f AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
