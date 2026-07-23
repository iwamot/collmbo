FROM dhi.io/python:3.14.6-debian13-dev@sha256:1df3badfd28c3fd54fb8371d55a4a050c4051b8a808f8367f7241442a334928b AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.31-debian13-dev@sha256:cc1ed23e8b2492fda45bb59ba1f08762ae3984aa5f89a4dba823a1ba47cf54e2 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:c43e37b1d2c740bf924149f7ce015a79636a084a3fd755ac8c5ffc2f4a850b3e AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
