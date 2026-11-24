FROM dhi.io/python:3.14.10-debian13-dev@sha256:a33fca17ad6c870cf02b9bd8e88fba7c16f3cd3b79cc3f5d2805759576646e2c AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.9-debian13-dev@sha256:545b93d8f69b358d4c72f2dd9d01e0c0c5992e4f70e474752aa2da9749fcfc36 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:f11473f548b1d047acaf942034495b495f0c50a208464b03eb94616071669fed AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
