FROM dhi.io/python:3.14.4-debian13-dev@sha256:9ccbbed8e0518436d173f8ac486ee8737bf0577b87b43a95710c9467b067f784 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.6-debian13-dev@sha256:4b70dedb0988a3fa60826a63c27c85c4be816e9faa1342e77587bd21c74c8630 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:16115a2626bfdb873847b12d70180dff4bd5edf7fc1f54e60ca33668c773b547 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
