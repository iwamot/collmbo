FROM dhi.io/python:3.14.7-debian13-dev@sha256:4c0f2439fe118fa2b59b7276779654a8f0940b6c6d419e4e48bba7d902a31224 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.4-debian13-dev@sha256:c3cead4817bfaadbab027a8d71d2f1cec676c595aeda583ebc379aa3717bb80d /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:70dd4833ac657817f0abbd1b84b965bc4c190a2b2f348d53218689f8e7f1f681 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
