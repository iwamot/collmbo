FROM dhi.io/python:3.14.8-debian13-dev@sha256:2862b68470650afe57e569b24695d6df9184105ee298fdf83ca7572ea076fe5e AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.22-debian13-dev@sha256:051d45fa34a3c6ec2ff5424931199c0de74db075cd439dcb9eaa0a9d054bc8f0 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:af4a57e4ddb13cca66efe38402e526436befcdd3139823054ad3edbeabda6a75 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
