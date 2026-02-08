FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY ./service_crawler/requirements.txt ./service_crawler/requirements.txt
RUN pip install --no-cache-dir -r ./service_crawler/requirements.txt

COPY ./common/ ./common
COPY ./service_crawler ./service_crawler
COPY ./proto ./proto
COPY ./build_protobufs.sh .

RUN chmod +x build_protobufs.sh && ./build_protobufs.sh

EXPOSE 8000

CMD ["python", "-m", "service_crawler.src.main"]
