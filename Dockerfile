FROM dhi.io/python:3.14.10-debian13-dev@sha256:490a2607efe2d8234b16da40c41fbca6d12799f046bf0def488ce868fc5b43da AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.6-debian13-dev@sha256:5bf4cb017668dc327dd04a802988b22671e9fce1088e255453ce72679293144f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:238eb9b564c3eec6de43cdaddfee6d92f946ae38a367d763c5e2fec4472a4814 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
