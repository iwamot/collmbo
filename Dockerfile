FROM dhi.io/python:3.14.7-debian13-dev@sha256:163babeca6942d098d8fc891223485636c8da5ad49e615c6f5bafd70d75677c7 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.15-debian13-dev@sha256:67572bf6db01bb0b9dae9d74bd4c98f3b8f4e0e24d7bc9ae737275c6bbdad95b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:f59b1caff475a5fe8f54159b4e95013329d24ee583d6f869a68ded79b661b17d AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
