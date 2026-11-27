FROM dhi.io/python:3.14.10-debian13-dev@sha256:6f93a60de8da16943f4b3ab684b64a6f4ef362d42b17d4a96775692bcd7954b4 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.10-debian13-dev@sha256:79d5364d32a28d7191ece4185199e10f88cf3b31a82ad34ff73a806955ae9f7f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:580f67ef645c65300576a58b6550431e2377e27ee9e4779e9fdc9606d5740bb8 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
