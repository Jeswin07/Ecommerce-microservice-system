from fastapi import FastAPI
from pydantic import BaseModel
import redis
import json
import time
import logging
import requests

from database import engine, SessionLocal
from models import ProductDB

from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
from pythonjsonlogger import jsonlogger


app = FastAPI()

# LOGGER SETUP
logger = logging.getLogger("product-service")

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter() # type: ignore

logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)


def send_log_to_es(log_data):
    try:
        requests.post("http://elasticsearch:9200/logs/_doc", json=log_data)
    except:
        pass


#  REDIS

r = redis.Redis(host="redis", port=6379, decode_responses=True)

# DATABASE
ProductDB.metadata.create_all(bind=engine)


# METRICS
REQUEST_COUNT = Counter("request_count", "Total API Requests")
REQUEST_LATENCY = Histogram("request_latency_seconds", "Request latency")


# MODEL

class Product(BaseModel):
    id: int
    name: str
    price: float


#  CREATE PRODUCT

@app.post("/products")
def create_product(product: Product):

    logger.info("Creating product", extra={"product_id": product.id})

    send_log_to_es({
        "service": "product-service",
        "event": "create_product",
        "product_id": product.id
    })

    db = SessionLocal()

    db_product = ProductDB(
        id=product.id,
        name=product.name,
        price=product.price
    )

    db.add(db_product)
    db.commit()
    db.close()

    # Write-through cache
    r.set(f"product:{product.id}", json.dumps(product.dict()))

    return {"message": "Product created"}


# GET PRODUCT

@app.get("/products/{product_id}")
def get_product(product_id: int):

    logger.info("Fetching product", extra={"product_id": product_id})

    send_log_to_es({
        "service": "product-service",
        "event": "get_product",
        "product_id": product_id
    })

    # Cache check
    cached = r.get(f"product:{product_id}")

    if cached:
        print("FROM CACHE ⚡")
        return json.loads(cached) # type: ignore

    db = SessionLocal()
    product = db.query(ProductDB).filter(ProductDB.id == product_id).first()
    db.close()

    if not product:
        return {"error": "Product not found"}

    result = {
        "id": product.id,
        "name": product.name,
        "price": product.price
    }

    # Cache update
    r.set(f"product:{product_id}", json.dumps(result))

    print("FROM DB 🐢")

    return result


# METRICS MIDDLEWARE

@app.middleware("http")
async def track_metrics(request, call_next):
    REQUEST_COUNT.inc()

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    REQUEST_LATENCY.observe(duration)

    return response


# PROMETHEUS ENDPOINT

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type="text/plain")