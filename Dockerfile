FROM dhi.io/python:3.14.10-debian13-dev@sha256:331fffd6ff7fcf9bf5f7dbde8d48fad634375baa739d1db23f65e0ec83bcd198 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.9-debian13-dev@sha256:b1368960e22a8261508bde6206b432f5a6c4113861add364ebf6acee41d9ae50 /uv /usr/local/bin/uv
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
