FROM dhi.io/python:3.14.10-debian13-dev@sha256:e84d616360a8ca598446289cadeeeaba36aa7d6e5d83878923e0c6123b268b0f AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.9-debian13-dev@sha256:ae33f5c3fa1cfd43942cae31d8258b6ec616d0340342e7bd0a248588ea76729c /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:5578c04c489778984cdf8a2ea90ddbe657ef898bd617db51b6dd53343a0b15bf AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
