# 🚀 Real-Time Order Processing System

A scalable, event-driven microservice architecture for processing orders in real-time using FastAPI, RabbitMQ, PostgreSQL, and Redis with Kubernetes support.

## ⚡ Why This Project?

- **Event-Driven Architecture** that scales with your business
- **Real-Time Processing** for immediate order feedback
- **Resilient Design** that handles failures gracefully
- **Comprehensive Monitoring** for system visibility
- **Kubernetes Support** for cloud-native deployments

## 🏗️ Tech Stack

- **FastAPI** - High-performance Python web framework
- **RabbitMQ** - Robust message broker for event processing
- **PostgreSQL** - Reliable relational database
- **Redis** - In-memory caching for speed
- **Docker** - Containerization for consistent environments
- **Kubernetes** - Container orchestration for scalable deployments

## 🔍 Key Features

- Complete order lifecycle management (create → pay → ship → deliver)
- Multiple pricing strategies with the Strategy Pattern
- Distributed caching for product information
- Comprehensive event system with automatic retries
- Rate limiting and idempotent API design
- Kubernetes deployment for production-ready scaling

## 🚀 Quick Start

### Docker Compose (Development)

```bash
# Clone the repository
git clone https://github.com/your-username/real-time-order-processing.git

# Create .env file (see docs/configuration.md for details)
cp .env.example .env

# Start all services
docker-compose up -d

# Access API documentation
open http://localhost:8000/docs
```

### Kubernetes (Production)

```bash
# Start Minikube (for local k8s development)
minikube start

# Configure Docker to use Minikube's Docker daemon
eval $(minikube docker-env)

# Deploy to Kubernetes
make k8s-deploy

# Access API documentation
make open-api
```

### 🧭 Accessing the Database with PgAdmin

For easy inspection and debugging of your PostgreSQL data, PgAdmin is included in the development setup.

- PgAdmin URL: [http://localhost:5050](http://localhost:5050)
- Default Credentials:
  - **Email**: `admin@admin.com`
  - **Password**: `admin`

#### 💡 Connect to PostgreSQL in PgAdmin

When adding a new server, use the following settings:

| Field        | Value              |
|--------------|--------------------|
| **Name**     | `postgres`         |
| **Host**     | `postgres`         |
| **Port**     | `5432`             |
| **Username** | `user`             |
| **Password** | `password`         |
| **Database** | `orders_db`        |

Once connected, you can explore the `products`, `orders`, `line_items`, etc.

#### 🛠️ CLI Shortcut (Makefile)

You can quickly open PgAdmin in your browser:

```bash
make pgadmin-open
```

## 📖 Documentation

- [System Architecture](docs/system_architechture.md)
- [API Endpoints](http://localhost:8000/docs)
- [Business logic](docs/business_logic.md)
- [RabbitMQ debuggin](docs/rabbitmq_consumer_debuggin.md)
- [Kubernetes Deployment Guide](docs/deployment_guide.md)

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit a pull request with your changes.


## 📝 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Author

**Sebastián Dávila**

Feel free to contribute, open issues, or suggest improvements! 🚀

