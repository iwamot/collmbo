FROM dhi.io/python:3.14.10-debian13-dev@sha256:8935d5e6a742a81370a2d5b36cc76271b10700ddd841787666667f107a51390c AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.7-debian13-dev@sha256:9498b4fafdf893784f7345bf79f918a7c909648a22487287932d94a05b18d0eb /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:46ab6a5ef9a6f48bf959dbd20bf3b56fad04cb32ed597481142ec61d42d816b1 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
