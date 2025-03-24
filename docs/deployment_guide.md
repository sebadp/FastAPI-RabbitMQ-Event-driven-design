# Kubernetes Deployment Guide

This document provides detailed instructions for deploying the Real-Time Order Processing System on Kubernetes.

## Prerequisites

- [Minikube](https://minikube.sigs.k8s.io/docs/start/) (for local development)
- Docker installed and running
- Python 3.9+ (only needed for local development)
- Kubernetes CLI (`kubectl`) installed
- Docker configured to build inside Minikube:
  ```bash
  eval $(minikube docker-env)
  ```

## Project Structure

The Kubernetes configuration files are organized in the `k8s/` directory:

```
k8s/
├── configmap-env.yml       # Environment variables for all services
├── fastapi-deployment.yml  # FastAPI API service deployment
├── postgres-deployment.yml # PostgreSQL database deployment
├── rabbitmq-deployment.yml # RabbitMQ message broker deployment
├── redis-deployment.yml    # Redis cache deployment
├── consumers-deployment.yml # Event consumers deployment
├── services.yml            # Service definitions for all components
├── job-test-connection.yml # Test job for verifying connectivity
└── scripts/
    └── test_connection.py  # Python script to test connections
```

## Deployment Guide

### Starting Minikube

For local development, start Minikube:

```bash
minikube start
```

### Building Docker Images

To build the Docker images inside Minikube:

```bash
# Configure Docker to use Minikube's Docker daemon
eval $(minikube docker-env)

# Build the images
make build
```

### Deploying the Application

Deploy all components to your Kubernetes cluster:

```bash
make k8s-deploy
```

This command:
1. Creates namespace if it doesn't exist
2. Applies all configuration from the `k8s/` directory
3. Sets up the following resources:
   - ConfigMap with environment variables
   - Deployments for FastAPI, PostgreSQL, RabbitMQ, Redis, and Consumers
   - Services for accessing each component

### Accessing the Application

Access the FastAPI Swagger UI:

```bash
make open-api
```

This opens your default browser with the API documentation.

### Testing Connectivity

Test RabbitMQ connectivity:

```bash
make test-rabbitmq
```

This runs a Kubernetes Job that attempts to connect to RabbitMQ and reports success or failure.

### Viewing Logs

View logs from the FastAPI deployment:

```bash
make logs-api
```

To view logs from other components:

```bash
# View RabbitMQ logs
kubectl logs -l app=rabbitmq

# View Consumer logs
kubectl logs -l app=event-consumers

# View PostgreSQL logs
kubectl logs -l app=postgres
```

### Seeding Sample Data

Seed the database with sample data:

```bash
make seed
```

By default, this creates:
- 10 random products
- 5 sample orders (with 1-3 items each)

You can customize the amounts:

```bash
make seed NUM_PRODUCTS=25 NUM_ORDERS=15
```

### Cleanup

To remove all deployed resources:

```bash
make k8s-destroy
```

## Available Makefile Commands

| Command | Description |
|---------|-------------|
| `make build` | Builds Docker images inside Minikube |
| `make k8s-deploy` | Deploys all components to the cluster |
| `make open-api` | Opens the FastAPI Swagger UI in your browser |
| `make test-rabbitmq` | Tests RabbitMQ connectivity |
| `make logs-api` | Shows logs from the FastAPI deployment |
| `make seed` | Seeds the database with sample data |
| `make k8s-destroy` | Deletes all Kubernetes resources |
| `make help` | Lists all available commands |

## Configuration

### Environment Variables

All environment variables are defined in `k8s/configmap-env.yml`. Key configurations include:

- Database connection settings
- RabbitMQ credentials
- Redis connection details
- API settings and feature flags

### Resource Limits

Each deployment specifies resource requests and limits to ensure proper scheduling and prevent resource starvation:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "100m"
  limits:
    memory: "512Mi"
    cpu: "200m"
```

Adjust these values based on your cluster's capacity and application requirements.

## Scaling

To scale the number of FastAPI or Consumer replicas:

```bash
# Scale FastAPI to 3 replicas
kubectl scale deployment fastapi-app --replicas=3

# Scale Consumers to 5 replicas
kubectl scale deployment event-consumers --replicas=5
```

## Production Considerations

For production environments:

1. Use a managed Kubernetes service (EKS, GKE, AKS)
2. Configure persistent volumes for PostgreSQL and RabbitMQ
3. Set up Horizontal Pod Autoscalers for FastAPI and Consumers
4. Implement proper secrets management instead of ConfigMaps for sensitive data
5. Configure ingress controllers and TLS certificates
6. Set up monitoring and alerting with Prometheus and Grafana
7. Implement proper backup strategies for the database

## Troubleshooting

### Common Issues

#### Pods Stuck in Pending State
- Check available resources: `kubectl describe node`
- Check events: `kubectl get events`

#### Connection Failures
- Verify services are running: `kubectl get services`
- Check pod status: `kubectl get pods`
- Examine pod logs: `kubectl logs <pod-name>`

#### Database Migration Issues
- Check the Alembic migration logs: `kubectl logs <fastapi-pod-name>`
- Manually connect to PostgreSQL: 
  ```bash
  kubectl exec -it <postgres-pod-name> -- psql -U user orders_db
  ```