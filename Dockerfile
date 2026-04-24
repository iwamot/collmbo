FROM dhi.io/python:3.14.4-debian13-dev@sha256:1f6554d34550a8f3a62a36aab197d266111798018af18bcc852128a970f2cc5b AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.7-debian13-dev@sha256:2f0a1134997f1eaa806ceda69e3d9b92f6c6c0d035342e19271949b2c78e1aed /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:e9075a8ed1e69e7573dab493947ca58bdea64409603544cd65f2d37619131165 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
