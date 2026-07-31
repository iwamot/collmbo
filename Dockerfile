FROM dhi.io/python:3.14.6-debian13-dev@sha256:15bf794abbbe30567641eb4d302a24a47e544673ca2a780caa005687ce28b47b AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.0-debian13-dev@sha256:7b6fe997ee81fd2f5e67d69a8af3b17ec58271ce4aee592890629b78998de1bb /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:a48b4d2f444300b14ca90979f44e920657f09e7f649d9251878af7438874df63 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
