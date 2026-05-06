# Microservices-Based E-Commerce System

This project implements a microservices-based e-commerce backend system that demonstrates real-world architectural practices. These practices include service isolation, asynchronous communication, caching, monitoring, and centralized logging. The system is designed to simulate a production-grade backend using industry-standard tools and technologies.

## Objectives

* To design and implement a microservices architecture.
* To enable independent service deployment and scaling.
* To implement asynchronous communication using message queues.
* To improve performance using caching mechanisms.
* To integrate monitoring and logging systems.
* To implement distributed request tracing.

## Technologies Used

* **Backend Framework**: FastAPI
* **Database**: PostgreSQL
* **Cache**: Redis
* **Message Queue**: RabbitMQ
* **Monitoring & Visualization**: Prometheus and Grafana
* **Logging & Analysis**: Elasticsearch and Kibana
* **Containerization**: Docker

## System Components

* **API Gateway**: Acts as the central entry point for all requests. It handles authentication via JWT, routing, rate limiting, and load balancing. It also adds a `request_id` for distributed tracing.
* **User Service**: Handles user registration and login. It operates a stateless authentication system by generating JWT tokens.
* **Product Service**: Manages product data using PostgreSQL for persistent storage and Redis as a caching layer. It implements a cache-first strategy utilizing read-through and write-through mechanisms.
* **Order Service**: Receives order requests and ensures non-blocking processing. It sends order data to a queue instead of directly writing to the database.
* **Worker Service**: Consumes messages from RabbitMQ to process orders asynchronously. It then stores the processed data in PostgreSQL.

## System Workflow

* **Product Flow**: Client → Gateway → Product Service → Redis (check) → DB (if miss) → Cache update.
* **Order Flow**: Client → Gateway → Order Service → RabbitMQ → Worker → PostgreSQL.

## Observability

* **Monitoring**: A `/metrics` endpoint is scraped by Prometheus, and Grafana dashboards visualize system performance trends. Metrics include request count and latency.
* **Logging**: Structured logs in JSON format are sent to Elasticsearch, and Kibana is used for log visualization and searching.
* **Tracing**: A unique request ID is passed via headers to enable full request lifecycle tracking across services, which is highly useful for debugging.

## Future Enhancements

* Replace RabbitMQ with Kafka.
* Add Logstash or Fluent Bit for a fully decoupled logging pipeline.
* Implement Kubernetes deployment and a CI/CD pipeline.
* Implement service discovery using Consul.
* Add API rate limiting using Redis.
