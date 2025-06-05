FROM python:3.13.4-slim-bookworm AS builder
ARG FLAVOR=slim
WORKDIR /build/
COPY ${FLAVOR}-requirements.txt /build/requirements.txt
RUN pip install --no-cache-dir -U pip
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.13.4-slim-bookworm AS app
WORKDIR /app/
COPY *.py /app/
COPY app/*.py /app/app/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
ENTRYPOINT [ "python", "main.py" ]
