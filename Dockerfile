FROM dhi.io/python:3.14.5-debian13-dev@sha256:98f54e1d2ba526f945659f512f21e94c76bc750c0b7935cb75995e22939beb86 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.17-debian13-dev@sha256:5b70efa969fdde0a3607bbc64eb1f79a6c396b91087ad02085a4a56d93cb197b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.5-debian13@sha256:ff889c0f24838055e6b1343a3c11abee14ec639d885efd257e7e636c0d1de6cc AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
