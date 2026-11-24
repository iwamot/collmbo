FROM dhi.io/python:3.14.10-debian13-dev@sha256:112e8169ae4315de4031bbc40f9747845cc1d22739445cd51634b1efe0d772a2 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.9-debian13-dev@sha256:e1731edb249509b4aac438d96c32084969c1164ad3c95643861fd233678e621c /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:2882c07f5e7ccb95b6610b897496e984ef39916702f9dcfd4a97ac4b19f82863 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
