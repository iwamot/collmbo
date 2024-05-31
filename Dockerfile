FROM python:3.11.4-slim-buster as builder
ARG USE_BEDROCK=false
COPY requirements.txt /build/
WORKDIR /build/
RUN if [ "$USE_BEDROCK" = "true" ]; then \
        echo boto3 >> requirements.txt; \
    fi \
    && pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r requirements.txt

FROM python:3.11.4-slim-buster as app
WORKDIR /app/
COPY *.py /app/
RUN mkdir /app/app/
COPY app/*.py /app/app/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder /usr/local/lib/ /usr/local/lib/
ENTRYPOINT [ "python", "main.py" ]
