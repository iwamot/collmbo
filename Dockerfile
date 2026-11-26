FROM dhi.io/python:3.14.10-debian13-dev@sha256:bc56234775ad310962009c99d2f2545dfc69a16549fefe8f2708d5ad680c5a16 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.9-debian13-dev@sha256:85c427cebefa73be84920a56fcf4628263c2b3a19bfc4e1c850ea7e4383a5a12 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:ae441722899efd2b1f2956d9f3e2ae623aac679d8ebe81e0077f8b10416d1a63 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
