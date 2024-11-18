FROM python:3.12.7-slim-bookworm AS builder
ARG USE_BEDROCK=false
COPY requirements.txt /build/
WORKDIR /build/
RUN pip install --no-cache-dir -U pip
RUN if [ "$USE_BEDROCK" = "true" ]; then \
        echo boto3 >> requirements.txt; \
    fi
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12.7-slim-bookworm AS app
WORKDIR /app/
COPY *.py /app/
COPY app/*.py /app/app/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
ENTRYPOINT [ "python", "main.py" ]
