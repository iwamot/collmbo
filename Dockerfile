FROM dhi.io/python:3.14.7-debian13-dev@sha256:ce3fd47fcdee41b6a6eb056108837ed181e06559c8cdd713e22f105f9f714e11 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.5-debian13-dev@sha256:220719b42f3296e70bc6a80b658b09b9686503fafcf23b4fd07b5622790801a3 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:b7d1a17506b26aeb669d02517c62864fb7f7b165be45e48fde79bd42b9ff291e AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
