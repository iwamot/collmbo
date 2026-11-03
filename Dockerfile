FROM dhi.io/python:3.14.10-debian13-dev@sha256:e1c528dee57ce33c3192099679a1690a1541030f5137df3587d3ed0454a172b6 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.6-debian13-dev@sha256:131dfb28ea9a3fd02dbc802daa9d64b4bc0c5b85ae6956bfc1462584b83be7c3 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:62b05a613f5a59e0ea78fff2b6131ce4264d0c7371c54134a34732beeb657e47 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
