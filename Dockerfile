FROM dhi.io/python:3.14.7-debian13-dev@sha256:db022e3dead75d1e4d262eaad6b7465bc320687a927015fd98488b2ea9c7e65c AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.10-debian13-dev@sha256:8405337907391a3cff201d08fd33af8d27dee79cd3f511317d3e0f9b46f96aca /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:f965b2c477d44c80c2cc6763a9d42617889dcfb5b94b5b4d5e8e38751155322f AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
