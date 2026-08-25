FROM dhi.io/python:3.14.7-debian13-dev@sha256:bc8161a12cca8610649d851d9af964779875c89c080e166ac41b925a31ea1626 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.5-debian13-dev@sha256:7dbb65f5b3386d3fe46e9f04821ce873ee089f4787da06c3026ae81ee977ad56 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:90dda111ab0b6667b9321d800e426120a9d4a39c73390825479caca4520e5fad AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
