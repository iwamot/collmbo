FROM dhi.io/python:3.14.5-debian13-dev@sha256:62437cf10be286437cf85add8d33672bf0597cefb3d23510bd3be8040f0b3105 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.19-debian13-dev@sha256:aae0ea3fcad97de49af19008aa3dbf876c9f572413bd4d69ea1ecdbf7be5052f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.5-debian13@sha256:93439cc97ac9680421f21294bc7b223478d1a4be70ec38781084f154784c6ad4 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
