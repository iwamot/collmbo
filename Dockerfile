FROM dhi.io/python:3.14.10-debian13-dev@sha256:c6d05bf1e567744820f780f4c5c9c8a5015a151f7f28aafc7a0ca04f4cb24602 AS builder
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
