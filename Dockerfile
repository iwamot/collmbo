FROM dhi.io/python:3.14.7-debian13-dev@sha256:95deb75d9e38b42eb57fa60e94285fa69a80b000de2e4730ba5313db1b5a4bc9 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.13-debian13-dev@sha256:8705d2524494822d15ab2ecb6d3d31acb9b43d52be8f0f5ed8e084ff2a82173b /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:5e1e7ddf4efddd05e414390978128730799d4150738c75060364228a073741ec AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
