FROM dhi.io/python:3.14.8-debian13-dev@sha256:c73dad82bf13f79fc2677318eb95c4a76c5920635d1177a2618da621c8953fbd AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.1-debian13-dev@sha256:8e8d4ecb8fded6c1cfb53e01462746c4d07be02fa33b079eae85805c914fc417 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:4622eb60ca1ee09577f69289bb79b9e9e31a1386a3802f1b2b9d0d66742f9a36 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
