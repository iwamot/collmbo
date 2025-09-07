FROM python:3.13.7-slim-bookworm AS builder
WORKDIR /build/
RUN apt-get update \
 && apt-get install -y --no-install-recommends cargo rustc \
 && rm -rf /var/lib/apt/lists/*
COPY uv-requirements.txt /build/
RUN pip install --no-cache-dir -r uv-requirements.txt
COPY requirements.txt /build/
RUN uv pip install --system --no-cache -r requirements.txt

FROM python:3.13.7-slim-bookworm AS app
WORKDIR /app/
COPY *.py /app/
COPY app/*.py /app/app/
COPY config/ /app/config/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
ENTRYPOINT [ "python", "main.py" ]
