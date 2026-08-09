FROM dhi.io/python:3.14.6-debian13-dev@sha256:b169ca0f1a662c049d238f507b6590c2804435334b4f3c036a73de2093b798f2 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.3-debian13-dev@sha256:e73fa8c883220b83de607f6b8fbe787063d0057c7d7efd5db05d320d7ef499e1 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:7fa71fa6509c110456742c8505dfea44f0b4656018123b3eaf4f33f71ae902b7 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
