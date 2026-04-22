FROM dhi.io/python:3.14.4-debian13-dev@sha256:9ccbbed8e0518436d173f8ac486ee8737bf0577b87b43a95710c9467b067f784 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.7-debian13-dev@sha256:32e7fc3618750b495d6ab5b91460a7beeeaa037a3e505bc1973ad5868db72a4c /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:eca8d67bc52bcae66bb74a924708ef58b866f229ae3b1e79c2bd24cb2f4c304f AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
