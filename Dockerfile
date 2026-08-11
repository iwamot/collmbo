FROM dhi.io/python:3.14.6-debian13-dev@sha256:4e6d70f6819594aa6210ba629695eaec7e56f72cd1ec0dca22e9cf0699ff01d7 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.3-debian13-dev@sha256:e73fa8c883220b83de607f6b8fbe787063d0057c7d7efd5db05d320d7ef499e1 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:8f20a4c351f7d4b8fc89b10d04d6089adac166e14aa4953b301db5b3a3b07ea2 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
