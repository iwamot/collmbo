FROM dhi.io/python:3.14.8-debian13-dev@sha256:5b7724d3ca177d536fe88db1de8c900f29671f2cca613358e618567acfe526b2 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.1-debian13-dev@sha256:8e8d4ecb8fded6c1cfb53e01462746c4d07be02fa33b079eae85805c914fc417 /uv /usr/local/bin/uv
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
