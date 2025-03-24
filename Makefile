# Variables
PROJECT_NAME=real-time-order-processing
IMAGE_NAME=$(PROJECT_NAME):latest
K8S_DIR=k8s
NUM_PRODUCTS ?= 10
NUM_ORDERS ?= 5
# Build Docker image (local for Minikube)
build:
	@echo "🚧 Building Docker image..."
	eval $$(minikube docker-env) && docker build -t $(IMAGE_NAME) .

# Apply all Kubernetes manifests
k8s-deploy: build
	@echo "🚀 Applying Kubernetes manifests..."
	kubectl apply -f $(K8S_DIR)/configmap-env.yml
	kubectl apply -f $(K8S_DIR)/rabbitmq-deployment.yml
	kubectl apply -f $(K8S_DIR)/postgres-pvc.yml
	kubectl apply -f $(K8S_DIR)/postgres-deployment.yml
	kubectl apply -f $(K8S_DIR)/redis-deployment.yml
	kubectl apply -f $(K8S_DIR)/fastapi-deployment.yml
	kubectl apply -f $(K8S_DIR)/consumers-deployment.yml
	kubectl apply -f $(K8S_DIR)/services.yml

# Access FastAPI via browser
open-api:
	@echo "🌐 Opening FastAPI in browser..."
	minikube service fastapi

# Run connection test job
test-rabbitmq:
	kubectl apply -f $(K8S_DIR)/job-test-connection.yml
	kubectl logs job/test-rabbitmq-connection

# Tear down everything
k8s-destroy:
	@echo "🧹 Deleting Kubernetes resources..."
	kubectl delete -f $(K8S_DIR)

# Check app logs
logs-api:
	kubectl logs deployment/fastapi


seed-local:
	@echo "🌱 Seeding locally: Products=$(NUM_PRODUCTS), Orders=$(NUM_ORDERS)"
	docker-compose run --rm \
		-e NUM_PRODUCTS=$(NUM_PRODUCTS) \
		-e NUM_ORDERS=$(NUM_ORDERS) \
		seed

# Abrir PgAdmin en el navegador
pgadmin-open:
	open http://localhost:5050

# Ver logs de PgAdmin
pgadmin-logs:
	docker-compose logs -f pgadmin

# Help
help:
	@echo ""
	@echo "⚙️  Comandos disponibles:"
	@echo "  make build            → Build Docker image para Minikube"
	@echo "  make k8s-deploy       → Desplegar todo en Kubernetes"
	@echo "  make open-api         → Abrir la API en navegador"
	@echo "  make test-rabbitmq    → Ejecutar test de conexión a RabbitMQ"
	@echo "  make k8s-destroy      → Borrar todos los recursos de Kubernetes"
	@echo "  make logs-api         → Ver logs del FastAPI"
	@echo "  make seed-local       → Sembrar datos localmente"
	@echo "  make pgadmin-open     → Abrir PgAdmin en el navegador"
	@echo "  make pgadmin-logs     → Ver logs de PgAdmin"
	@echo ""
