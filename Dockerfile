FROM dhi.io/python:3.14.10-debian13-dev@sha256:815473d51ee1c662a73445bac955ae0c9137e1afc4b1ffba853a2e7d6f2fb393 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.9-debian13-dev@sha256:56f94ca0d240c24f79e196c3cdb746a6826ee9809b3c3cdeeca840f33da886f2 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:ac22a260bf67a83d70bd948c8ff7bb05822456510673ed6821e0f20e9003ae8c AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
