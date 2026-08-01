FROM dhi.io/python:3.14.6-debian13-dev@sha256:b1b502f0903fb63589bb660570872c94569a2475f3ff53597754257baff8d06c AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.1-debian13-dev@sha256:274f2d478e0ef8f6bced12bf085f641b27985db662e94d15871a348ab651e613 /uv /usr/local/bin/uv
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
