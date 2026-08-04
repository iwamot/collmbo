FROM dhi.io/python:3.14.6-debian13-dev@sha256:537798418beb6b35148cddf45e12fe55c5ea1c2da019545964b244e37cb65b97 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.1-debian13-dev@sha256:79a8007d99385ed9ea7d657a516acf36428848e0dfdfa2f3886a45de84200f32 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:f3c4e102e557c0eee652cfd14b7da473c89d9126a07f5b0ebd9f8e79183f4038 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
