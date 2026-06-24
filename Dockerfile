FROM dhi.io/python:3.14.6-debian13-dev@sha256:a8badc91a4f08b1d89cdcefcf2ab269effc49ac8f93c10bad949df443817d096 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.11.23-debian13-dev@sha256:fe6633385a16b30e9fe235f59deca72937f11a85ed89ca71b4d8fe2846fe2416 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.6-debian13@sha256:a48290584a7fcec5935cecf4093ab9f293e3d57b3617b356316c781744e218c7 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
