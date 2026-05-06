import pika
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import OrderDB
from database import Base

from sqlalchemy import Column, Integer
from database import Base

DATABASE_URL = "postgresql://admin:admin@localhost:5433/order_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(bind=engine)

def process_order(ch, method, properties, body):
    data = json.loads(body)

    print("Processing order:", data)

    db = SessionLocal()

    new_order = OrderDB(
        user_id=data["user_id"],
        product_id=data["product_id"]
    )

    db.add(new_order)
    db.commit()

    print("Order saved to DB")


connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='rabbitmq')
)

channel = connection.channel()
channel.queue_declare(queue='order_queue')

channel.basic_consume(
    queue='order_queue',
    on_message_callback=process_order,
    auto_ack=True
)

print("Worker started...")

channel.start_consuming()