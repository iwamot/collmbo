FROM dhi.io/python:3.14.7-debian13-dev@sha256:ea5b59c015fd5ea36f8acb7163b2972391ddf822716aab3a6f67326700be9ff1 AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.5-debian13-dev@sha256:35634f3fbf2061ae02a4411567b3476fb55718acfd502fdd8308974118b2b03f /uv /usr/local/bin/uv
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
