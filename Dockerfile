FROM dhi.io/python:3.14.8-debian13-dev@sha256:5b7724d3ca177d536fe88db1de8c900f29671f2cca613358e618567acfe526b2 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.0-debian13-dev@sha256:f3325c72fac229ebad410874bc44868787c8927fe794ac91e4d6158c1765eba6 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:b2dee88be07689a608f86c392dd863f20399f8ffcbe99eff6bdb4f04485d9298 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
