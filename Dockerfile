FROM dhi.io/python:3.14.5-debian13-dev@sha256:37be3fa9f01d355e5e3b51a866c711ec3731999e6f537ebe97d41facc85a58b9 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.19-debian13-dev@sha256:3d0f103f5c06bd7680ca051b28d854f8f79478faf56415b54b2530172ee75ed1 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.5-debian13@sha256:7b74640b7f36f4e32dccaddc497182f90f476f889323ab5626b7cffd67ba3c8a AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
