FROM dhi.io/python:3.14.8-debian13-dev@sha256:f6d19e0cb6f1d80a20f6b263e40a4089c94f54bf1c35f8e82c52ab9f38eeab4e AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.6-debian13-dev@sha256:16cd20e62a83616135c1caf4b0d66f5111def915ed7e051f40cac71c109e94f1 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:17b857996add4968cb749df5f1676f1c9c048412636da3b85dc6660151892b47 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
