#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=================================================="
echo "📦 Building E-Commerce Microservices Docker Images"
echo "=================================================="

# Check if minikube is running
IS_MINIKUBE=false
if command -v minikube &>/dev/null && minikube status &>/dev/null; then
    IS_MINIKUBE=true
    echo "💡 Minikube detected and running. Images will be automatically loaded into Minikube."
fi

SERVICES=(
    "auth-service:services/auth_service"
    "product-service:services/product_service"
    "payment-service:services/payment_service"
    "order-service:services/order_service"
    "notification-service:services/notification_service"
    "api-gateway:services/api_gateway"
)

for item in "${SERVICES[@]}"; do
    IFS=":" read -r name dir <<< "$item"
    tag="ecommerce/${name}:latest"
    echo "--------------------------------------------------"
    echo "🔨 Building ${tag} from ${dir}..."
    docker build -t "${tag}" "${ROOT_DIR}/${dir}"
    
    if [ "$IS_MINIKUBE" = true ]; then
        echo "📥 Loading ${tag} into Minikube..."
        minikube image load "${tag}"
    fi
    echo "✅ Successfully prepared ${tag}"
done

echo "=================================================="
echo "🎉 All 6 microservice images built and ready!"
echo "=================================================="
if [ "$IS_MINIKUBE" = true ]; then
    echo "Images inside Minikube:"
    minikube image ls | grep -E "ecommerce/(auth|product|payment|order|notification|api-gateway)" || true
else
    echo "Images in host Docker:"
    docker images | grep -E "^ecommerce/" || true
fi
