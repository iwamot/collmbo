FROM dhi.io/python:3.14.4-debian13-dev@sha256:eec5f7badfdcb6685d36f1316d543bf54be5f202511883cae8215f13600fb317 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.7-debian13-dev@sha256:2f0a1134997f1eaa806ceda69e3d9b92f6c6c0d035342e19271949b2c78e1aed /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.4-debian13@sha256:c68807a71f9271d0ff1898184a1f450c681a2f47feb5824fd6b33e70e1857ac1 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
