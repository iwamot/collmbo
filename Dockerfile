FROM dhi.io/python:3.14.10-debian13-dev@sha256:422c5e9568e37d64eac9f1d04dfc48ee7d7738272a983bdb35c2cf3ec4f4b5a6 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.9-debian13-dev@sha256:e5a2eb64936f9738340cfc21b2eed235fa226b3e9197f6d13ff34b503c3735da /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:f11473f548b1d047acaf942034495b495f0c50a208464b03eb94616071669fed AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
