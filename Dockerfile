FROM dhi.io/python:3.14.3-debian13-dev@sha256:de13b64e07a18bf0116a245c1ffcb1a5ef5cd6413eaf5568b9ea23be08e710ff AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.3-debian13-dev /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:6d3c68e4ccbf3f677a0da437117a7cbb22c6f865bf82dfd1d6a03b08aa243690 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
