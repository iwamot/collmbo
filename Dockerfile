FROM dhi.io/python:3.14.10-debian13-dev@sha256:405f74fad5143e4aedbcadf79acd7662f4613088beea3d3a08f103e478b96ade AS builder
WORKDIR /build/
COPY --from=dhi.io/uv:0.13.10-debian13-dev@sha256:79d5364d32a28d7191ece4185199e10f88cf3b31a82ad34ff73a806955ae9f7f /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /build/
RUN uv sync --frozen --no-dev

FROM dhi.io/python:3.14.10-debian13@sha256:61c3ac7b63b723222114de20e313bf2896646bf1057e5bba7f561c5161af52e4 AS app
WORKDIR /app/
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY config/ /app/config/
COPY main.py /app/
COPY app/ /app/app/
ENTRYPOINT [ "python", "main.py" ]
