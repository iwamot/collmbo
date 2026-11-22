FROM dhi.io/python:3.14.10-debian13-dev@sha256:fb8e904271cb45bd26ccbc105904265e445156c377365d5f755ac10ea0b0c7dc AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.9-debian13-dev@sha256:ae33f5c3fa1cfd43942cae31d8258b6ec616d0340342e7bd0a248588ea76729c /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:b4b801417be33962e814aaab2272d90874badd2bfc2044d6b5fea9176e3f70e9 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
