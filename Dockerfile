FROM dhi.io/python:3.15.2-debian13-dev@sha256:7adb7ee72808f31a875eff621c20965e0deff66cedec21199a01ea38378bda68 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.6-debian13-dev@sha256:d6d83d18e96a6ed138a3bfe270d1aba33ad4af5acbfb0f4815a77d92f6477cb6 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.15.2-debian13@sha256:dff2966bc273ff38fae6f84d21180d3265864611b4f805e44695449f11343d72 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
