FROM dhi.io/python:3.14.3-debian13-dev@sha256:b467acb33574167e866bb05d83ead3bdc1003982f3a5ec4353a1ef0dd7f378e8 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.8@sha256:88234bc9e09c2b2f6d176a3daf411419eb0370d450a08129257410de9cfafd2a /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:2142b2371e833b56445f99b3cbcfd2d955544cacdd49b00ddc3065aba827d98c AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
