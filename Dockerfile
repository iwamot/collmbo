FROM dhi.io/python:3.14.6-debian13-dev@sha256:3c5bdfca9edc21bbe3c3d1ff3b7dac2ef72fccaf146e7befcaf1c4c616edc010 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.20-debian13-dev@sha256:235660d8c52a9b678a11c44b72306e064171adc818b4bdfc344583e7228f3e0d /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:bac401290850569d359003252deba9d3fb9312c87c394e2ff400cc50ca8692fa AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
