from fastapi import FastAPI
from pydantic import BaseModel
import pika
import json

app = FastAPI()


# 📦 Request model
class Order(BaseModel):
    user_id: int
    product_id: int


# 🔹 Create order
@app.post("/orders")
def create_order(order: Order):
    message = {
        "user_id": order.user_id,
        "product_id": order.product_id
    }

    send_to_queue(message)

    return {
        "status": "success",
        "message": "Order sent to queue"
    }


# 🔹 Health check
@app.get("/")
def root():
    return {"message": "Order Service Running"}

def send_to_queue(message):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='rabbitmq')
    )
    channel = connection.channel()

    channel.queue_declare(queue='order_queue')

    channel.basic_publish(
        exchange='',
        routing_key='order_queue',
        body=json.dumps(message)
    )

    connection.close()