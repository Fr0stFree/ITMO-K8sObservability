FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY ./service_api/requirements.txt ./service_api/requirements.txt
RUN pip install --no-cache-dir -r ./service_api/requirements.txt

COPY ./common/ ./common
COPY ./service_api ./service_api
COPY ./proto ./proto
COPY ./build_protobufs.sh .

RUN chmod +x build_protobufs.sh && ./build_protobufs.sh

EXPOSE 8000

CMD ["python", "-m", "service_api.src.main"]
