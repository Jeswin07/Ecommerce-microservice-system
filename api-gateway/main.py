from fastapi import FastAPI, HTTPException, Depends, Request
import requests
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import time
import uuid
import logging
from pythonjsonlogger import jsonlogger

app = FastAPI()

# =========================
# 🔥 LOGGER SETUP
# =========================
logger = logging.getLogger("api-gateway")

handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter() # type: ignore
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.INFO)


def send_log_to_es(log_data):
    try:
        requests.post("http://elasticsearch:9200/logs/_doc", json=log_data)
    except:
        pass


# =========================
# 🔐 SECURITY
# =========================
security = HTTPBearer()

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# =========================
# ⚡ RATE LIMIT
# =========================
request_log = {}

def rate_limit(user_id: str):
    now = time.time()

    if user_id not in request_log:
        request_log[user_id] = []

    request_log[user_id] = [
        t for t in request_log[user_id] if now - t < 10
    ]

    if len(request_log[user_id]) >= 5:
        raise HTTPException(status_code=429, detail="Too many requests")

    request_log[user_id].append(now)


# =========================
# 🔁 REQUEST TRACING MIDDLEWARE
# =========================
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


# =========================
# 🌐 SERVICES
# =========================
USER_SERVICE = "http://127.0.0.1:8001"
PRODUCT_SERVICE = "http://127.0.0.1:8002"
ORDER_SERVICE = "http://127.0.0.1:8003"

PRODUCT_SERVICES = [
    "http://127.0.0.1:8002",
    "http://127.0.0.1:8004"
]

current_index = 0


def get_product_service():
    global current_index
    url = PRODUCT_SERVICES[current_index]
    current_index = (current_index + 1) % len(PRODUCT_SERVICES)
    return url


# =========================
# 🏠 ROOT
# =========================
@app.get("/")
def root():
    return {"message": "API Gateway Running"}


# =========================
# 👤 USER SERVICE
# =========================
class User(BaseModel):
    username: str
    password: str


@app.post("/users/register")
def register(user: User, request: Request):
    request_id = request.state.request_id

    logger.info("User register", extra={"request_id": request_id})

    send_log_to_es({
        "service": "api-gateway",
        "event": "user_register",
        "request_id": request_id
    })

    response = requests.post(f"{USER_SERVICE}/users/register", json=user.dict())
    return response.json()


@app.post("/users/login")
def login(user: User, request: Request):
    request_id = request.state.request_id

    logger.info("User login", extra={"request_id": request_id})

    send_log_to_es({
        "service": "api-gateway",
        "event": "user_login",
        "request_id": request_id
    })

    response = requests.post(f"{USER_SERVICE}/users/login", json=user.dict())
    return response.json()


# =========================
# 📦 PRODUCT SERVICE
# =========================
class Product(BaseModel):
    id: int
    name: str
    price: float


@app.post("/products")
def create_product(product: Product, request: Request, user=Depends(verify_token)):
    request_id = request.state.request_id

    logger.info("Create product", extra={"request_id": request_id})

    send_log_to_es({
        "service": "api-gateway",
        "event": "create_product",
        "request_id": request_id
    })

    response = requests.post(
        f"{PRODUCT_SERVICE}/products",
        json=product.dict(),
        headers={"X-Request-ID": request_id}
    )

    return response.json()


@app.get("/products/{product_id}")
def get_product(product_id: int, request: Request, user=Depends(verify_token)):
    request_id = request.state.request_id

    service_url = get_product_service()

    logger.info("Get product", extra={
        "request_id": request_id,
        "product_id": product_id
    })

    send_log_to_es({
        "service": "api-gateway",
        "event": "get_product",
        "product_id": product_id,
        "request_id": request_id
    })

    response = requests.get(
        f"{service_url}/products/{product_id}",
        headers={"X-Request-ID": request_id}
    )

    return response.json()


# =========================
# 🧾 ORDER SERVICE
# =========================
class Order(BaseModel):
    user_id: int
    product_id: int


@app.post("/orders")
def create_order(order: Order, request: Request, user=Depends(verify_token)):
    request_id = request.state.request_id

    rate_limit(user["sub"])

    logger.info("Create order", extra={"request_id": request_id})

    send_log_to_es({
        "service": "api-gateway",
        "event": "create_order",
        "request_id": request_id
    })

    response = requests.post(
        f"{ORDER_SERVICE}/orders",
        json=order.dict(),
        headers={"X-Request-ID": request_id}
    )

    return response.json()