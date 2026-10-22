FROM dhi.io/python:3.14.8-debian13-dev@sha256:f342776dc2e3f2c3d9f37cf4cc182bbeb81b4eb4d3543357163aa5fa95bdc8bd AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.4-debian13-dev@sha256:ea40271559b60cd41db876f59fac4f8df62bab44a625e0afcdfdd9f375217a32 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.8-debian13@sha256:046a46512297187590b40b85e86ea2b128077d57601847ce916ecb7d919a7291 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
