FROM dhi.io/python:3.14.10-debian13-dev@sha256:331fffd6ff7fcf9bf5f7dbde8d48fad634375baa739d1db23f65e0ec83bcd198 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.8-debian13-dev@sha256:4d7b78533cefd5e5567bef51161e5cdf897499d149afc6c4c047c18608fb8fe9 /uv /usr/local/bin/uv
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
