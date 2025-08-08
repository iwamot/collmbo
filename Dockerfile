FROM python:3.13.6-slim-bookworm AS builder
ARG FLAVOR=slim
WORKDIR /build/
COPY *-requirements.txt /build/
RUN pip install --no-cache-dir -r uv-requirements.txt
RUN uv pip install --system --no-cache -r ${FLAVOR}-requirements.txt

FROM python:3.13.6-slim-bookworm AS app
WORKDIR /app/
COPY *.py /app/
COPY app/*.py /app/app/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
ENTRYPOINT [ "python", "main.py" ]
