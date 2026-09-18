FROM dhi.io/python:3.14.7-debian13-dev@sha256:d8b5d4db6510d666e22d4fa87d4545ad0bb11a7ef9ecb54aee40a12388a65ab9 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.15-debian13-dev@sha256:67572bf6db01bb0b9dae9d74bd4c98f3b8f4e0e24d7bc9ae737275c6bbdad95b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:71245bfb85e3632288e5f9816dd9fb809e65b10e1e20f25bedf4d1a92b0a4ddd AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
