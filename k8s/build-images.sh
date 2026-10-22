#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=================================================="
echo "📦 Building E-Commerce Microservices Docker Images"
echo "=================================================="

# Check if minikube is running; if so, point docker CLI to Minikube's daemon
if command -v minikube &>/dev/null && minikube status &>/dev/null; then
    echo "💡 Minikube detected and running. Pointing Docker environment to Minikube..."
    eval $(minikube docker-env)
else
    echo "ℹ️  Building images in local Docker daemon."
    echo "   (Note: If deploying to Minikube, start it first with 'minikube start' then run this script, or run 'eval \$(minikube docker-env)' before building)"
fi

build_image() {
    local name="$1"
    local dir="$2"
    local tag="ecommerce/${name}:latest"
    echo "--------------------------------------------------"
    echo "🔨 Building ${tag} from ${dir}..."
    docker build -t "${tag}" "${ROOT_DIR}/${dir}"
    echo "✅ Successfully built ${tag}"
}

build_image "auth-service" "services/auth_service"
build_image "product-service" "services/product_service"
build_image "payment-service" "services/payment_service"
build_image "order-service" "services/order_service"
build_image "notification-service" "services/notification_service"
build_image "api-gateway" "services/api_gateway"

echo "--------------------------------------------------"
echo "🎉 All 6 microservice images built successfully!"
echo "=================================================="
echo "Available ecommerce images:"
docker images | grep -E "^ecommerce/" || true
