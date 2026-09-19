FROM dhi.io/python:3.14.7-debian13-dev@sha256:cc2a26e03005f5eaa345a34efaa48d1c672186dc27b74bf566804ce7fd5b8afb AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.16-debian13-dev@sha256:8344b2b4c42899ea706992b4dba85bd58493183a28684438c555cde3b9080f23 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:71245bfb85e3632288e5f9816dd9fb809e65b10e1e20f25bedf4d1a92b0a4ddd AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
