FROM dhi.io/python:3.14.8-debian13-dev@sha256:debbc2a523d09b60d89c0d1f5792609a3cc8840726871b0ca278e9533a6c342e AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.4-debian13-dev@sha256:34076b552f25c0cd27ead5ddeb0ec82addc1ac5e8ab5d5ccf91bc6baa1528739 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:02aeafdfeb18e859d8ccb221c2ca8e23c54632fd79ce841359f9f06b646877b3 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
