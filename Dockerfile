FROM dhi.io/python:3.14.7-debian13-dev@sha256:02173cae8b920c98ff9fab81eb1aefcadd229f158110553c6ed758dc935589dd AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.12.4-debian13-dev@sha256:c3cead4817bfaadbab027a8d71d2f1cec676c595aeda583ebc379aa3717bb80d /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.7-debian13@sha256:0536ccad57c9be08128bd2a6f0982570086ec943a88033f4f53f7adffe407903 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
