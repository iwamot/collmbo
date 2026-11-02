FROM dhi.io/python:3.14.10-debian13-dev@sha256:e1c528dee57ce33c3192099679a1690a1541030f5137df3587d3ed0454a172b6 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.6-debian13-dev@sha256:5bf4cb017668dc327dd04a802988b22671e9fce1088e255453ce72679293144f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:7773fe0d15497d7dc20d59148261e81d968b0d8088b3074d8ff06b25a3e38b7b AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
