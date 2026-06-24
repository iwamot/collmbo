FROM dhi.io/python:3.14.6-debian13-dev@sha256:278a2051e1ccb1f349d1d9f86da9a5a3cb8e52c122ee6a9da278993ecbc1090b AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.23-debian13-dev@sha256:7e93efaa4fdda7d4a0ec1c68b0a556fdf0d39c7b9fe1dc5609193c2886f56aa3 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:f0e074dca2de2f27be6e3536b13fb8cd9e44764b22daac237b9cbf2c9982be59 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
