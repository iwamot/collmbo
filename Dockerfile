FROM dhi.io/python:3.14.7-debian13-dev@sha256:35263a6c329e601a836a011a27792d3ae84f387b9055b40035b0649d5ce68e3c AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.5-debian13-dev@sha256:7ec98149338b9d8665262c0009ebcc784a42008d74cd5ea30f8ef7e81e11da55 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:aa0ca597178dc1f272f15ed23a213becab317bd8c47af82694a497a51dc8cee6 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
