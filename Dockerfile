FROM dhi.io/python:3.14.3-debian13-dev@sha256:99c6d3c8839035ebf2b8f342af2a0053dd31f3126ccd720204f79e24aa1d2813 AS builder
WORKDIR /build/
COPY --from=ghcr.io/astral-sh/uv:0.10.12@sha256:72ab0aeb448090480ccabb99fb5f52b0dc3c71923bffb5e2e26517a1c27b7fec /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.3-debian13@sha256:516bc88f3c649a5e66c58f7a5e53ad915623f153a02118ae409e9565f3f928a2 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
