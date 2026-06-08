FROM dhi.io/python:3.14.5-debian13-dev@sha256:640e582c238a0f2cca3bd5d3c6175cee098c048a63bd58ff547490af6bc9dff2 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.19-debian13-dev@sha256:aae0ea3fcad97de49af19008aa3dbf876c9f572413bd4d69ea1ecdbf7be5052f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.5-debian13@sha256:98b76cc6b2727b4199456dafae189e52146d4fb6497d86be6b2c52ac99712094 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
