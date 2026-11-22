FROM dhi.io/python:3.14.10-debian13-dev@sha256:1fabe073bfa4496f791134f62fc2f67cd3bd1a491c85ce33a0f830d0e584164d AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.9-debian13-dev@sha256:b985f2f93e67f502965ba85273d8d8699a08dac41104cd0ae9d423ebea6b4ded /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:b2205596ee4ec89c3fe3e97cc1a141f54527863f9c581eea93042741811994bb AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
