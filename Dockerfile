FROM dhi.io/python:3.14.10-debian13-dev@sha256:d43af3feac6200c6d6ebd2000d8833779bd69260bb91d9035aaaa0b0635f705f AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.7-debian13-dev@sha256:050ebca4bfefd9f66547a44fc488fc9e9ed7718362ae8395f87434d805bb7b52 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:e21119acac57f9c336c0e7866ce8cfc61ef033e5db4c04d193e6df51088688d7 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
