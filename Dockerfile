FROM dhi.io/python:3.14.6-debian13-dev@sha256:15bf794abbbe30567641eb4d302a24a47e544673ca2a780caa005687ce28b47b AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.0-debian13-dev@sha256:f822b7116e857aaf8dc43ac4aae3b6d8767686d8ea9e1cbc0647f36ebf061591 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:f3c4e102e557c0eee652cfd14b7da473c89d9126a07f5b0ebd9f8e79183f4038 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
