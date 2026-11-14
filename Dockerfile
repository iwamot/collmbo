FROM dhi.io/python:3.14.10-debian13-dev@sha256:60dbebd00c5332a2d5984a96f33b76d6e42167095a9db8c49cd0038ac388de77 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.8-debian13-dev@sha256:4cdf9164c4def8ae1686b79a0648e9bc8096de0eb5b5941e38a103fd00211484 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:d20d953b545c83acd9e1b6b6b6d27cf14de38e6a39689334f71454c33cf41893 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
