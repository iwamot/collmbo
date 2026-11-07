FROM dhi.io/python:3.14.10-debian13-dev@sha256:4f0273dfbc2816cbe56de9bbb483699b4d0a0e824443fefb45e1dc7ff356b073 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.7-debian13-dev@sha256:25fb9e920eeff3140c667d0fcc92c28b6d22e57772a7a28af9b8827734edaded /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:46ab6a5ef9a6f48bf959dbd20bf3b56fad04cb32ed597481142ec61d42d816b1 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
