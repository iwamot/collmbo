FROM dhi.io/python:3.14.6-debian13-dev@sha256:1977c4a9624171ef582e641eb6f67adfc3f4b3ec0cb59345876f1928cda6f698 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.26-debian13-dev@sha256:861646dc49b81fedf923b5beae11d24a9ec5058e8b92af2afff8183f390a87a0 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:975fb771f0685d6e0aa1212813c6f0c8c5062e77aa4d34daa5aabbb9b9713f1d AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
