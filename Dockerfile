FROM dhi.io/python:3.14.4-debian13-dev@sha256:9ccbbed8e0518436d173f8ac486ee8737bf0577b87b43a95710c9467b067f784 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.4-debian13-dev@sha256:426f12af523c26ce458a76a1d8eaac150a816bebb38922c31a88d11ddedb14f3 /uv /usr/local/bin/uv
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
