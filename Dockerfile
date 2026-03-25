FROM python:3.11-alpine

EXPOSE 8080

WORKDIR /app

COPY server.py /app

ENV PORT=8080

CMD ["python", "server.py"]
