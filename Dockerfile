FROM dhi.io/python:3.14.7-debian13-dev@sha256:42cd56dede69350b250398097287cbf1020d0ead0ad8cb4e179bd3bac1a98634 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.19-debian13-dev@sha256:b817ed62340cdd37ef7cfb33c000fc738ba0565c841eade69612d9ce9c554db4 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:e1a5bd571d9585d7eb80c8278b54b69a0e0bf5a9bb2b1424b9e4576374df6659 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
