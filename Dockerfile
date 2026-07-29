FROM dhi.io/python:3.14.6-debian13-dev@sha256:6ed0e92633c8dba6e48cf0b44153ea027a221d73b882e489164a1569ec495658 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.32-debian13-dev@sha256:db69a0c4eda35ea1771c01db45227e7ea33673fc448a1b4a973a74ab1f1547be /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:ccbd15914b9221ffc506c66792c37e714cb59687f48aab3a69b27cd74df718a2 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
