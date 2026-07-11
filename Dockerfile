FROM dhi.io/python:3.14.6-debian13-dev@sha256:db7b1fd1f71d338efca2edf1faf5dd71dccad749431920344060d28ab51c748e AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.28-debian13-dev@sha256:0eaf00569b4691647374bfce93bbedc00f58f62f1fa91604e759519b719de63c /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:03a4890bd62398b60e80f0138d459308aa916d83fd783a6976d04c1767155f08 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
