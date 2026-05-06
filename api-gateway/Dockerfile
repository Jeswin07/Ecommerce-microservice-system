FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install fastapi uvicorn requests python-jose python-json-logger

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]