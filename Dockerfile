FROM dhi.io/python:3.14.10-debian13-dev@sha256:290766784d2488991d638bc8c52a53a3c5012513075da9b7bc67705510d7cb2d AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.7-debian13-dev@sha256:9498b4fafdf893784f7345bf79f918a7c909648a22487287932d94a05b18d0eb /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:edd23000cfe4bac2bf0186da278966fff7ff2ccb34d9ac4f8fc2ffb03317a2dc AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
