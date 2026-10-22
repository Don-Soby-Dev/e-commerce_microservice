# Kubernetes Deployment Guide for E-Commerce Microservices

This directory contains the production-ready Kubernetes manifests and tooling to deploy the entire E-Commerce microservices ecosystem on any Kubernetes cluster (such as **Minikube**, **Kind**, **EKS**, **GKE**, or self-hosted **K8s**).

---

## 🏛 Architecture Overview

All services run inside a dedicated namespace: `ecommerce`.

```
                    ┌───────────────────────────────────────────────┐
                    │               Kubernetes Ingress              │
                    │         (or NodePort on port 30003)           │
                    └───────────────────────┬───────────────────────┘
                                            │ :8003
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │            API Gateway (Django REST)          │
                    └───────┬───────────────┼───────────────┬───────┘
                            │               │               │
        :8002               │         :8001 │               │ :8000
        ┌───────────────────┘               ▼               └───────────────────┐
        ▼                         ┌───────────────────┐                         ▼
┌───────────────┐                 │  Product Service  │                 ┌───────────────┐
│ Auth Service  │                 │    (Django REST)  │                 │ Order Service │
│ (Django REST) │                 └─────────┬─────────┘                 │ (Django REST) │
└───────┬───────┘                           │                           └───────┬───────┘
        │                                   │                                   │
        │ :5432                             │ :5432                :50051 (gRPC)│ :5432
        ▼                                   ▼                                   ▼
┌─────────────────────────────────────────────────────────────┐         ┌───────────────┐
│               PostgreSQL 16 Multi-Database                  │         │Payment Service│
│              (auth_db, product_db, order_db)                │         │(Python gRPC)  │
│           PersistentVolumeClaim: postgres-pvc (2Gi)         │         └───────┬───────┘
└─────────────────────────────────────────────────────────────┘                 │
                                                                                │ AMQP :5672
                                            ┌───────────────────────────────────┼───────────┐
                                            │                                   ▼           ▼
                                            │         ┌─────────────────────────────────────────┐
                                            │         │           RabbitMQ 3 Management         │
                                            │         │       PersistentVolumeClaim: (1Gi)      │
                                            │         └────────────────────┬────────────────────┘
                                            │                              │
                                            │                              │ AMQP :5672
                                            │                              ▼
                                            │         ┌─────────────────────────────────────────┐
                                            │         │      Notification Service (Worker)      │
                                            │         │           (Python Consumer)             │
                                            └─────────┴─────────────────────────────────────────┘
```

### Components Summary

| Resource | File | Type | Ports / Details |
| :--- | :--- | :--- | :--- |
| **Namespace** | `00-namespace.yaml` | Namespace | `ecommerce` |
| **Secrets** | `01-secrets.yaml` | Secret | Passwords, Django keys, RSA public & private keys |
| **ConfigMap** | `02-configmap.yaml` | ConfigMap | Microservices DNS URLs, environments |
| **Postgres Init** | `03-postgres-init-configmap.yaml` | ConfigMap | Multi-DB initialization script (`auth_db`, `product_db`, `order_db`) |
| **Proto Stubs** | `04-protos-configmap.yaml` | ConfigMap | Precompiled Payment protobuf stubs mounted at `/protos` |
| **PostgreSQL** | `05-postgres.yaml` | Deployment & PVC & Service | Port `5432`, 2Gi persistent volume |
| **RabbitMQ** | `06-rabbitmq.yaml` | Deployment & PVC & Service | AMQP `5672`, Management UI `15672`, 1Gi persistent volume |
| **Auth Service** | `07-auth-service.yaml` | Deployment & Service | Port `8002`, mounts RSA keys at `/app/certs` |
| **Product Service** | `08-product-service.yaml` | Deployment & Service | Port `8001` |
| **Payment Service** | `09-payment-service.yaml` | Deployment & Service | gRPC Port `50051`, mounts proto stubs at `/protos` |
| **Order Service** | `10-order-service.yaml` | Deployment & Service | Port `8000`, mounts proto stubs at `/protos` |
| **Notification Service** | `11-notification-service.yaml` | Deployment | RabbitMQ consumer worker |
| **API Gateway** | `12-api-gateway.yaml` | Deployment & NodePort Service | ClusterIP `8003`, NodePort `30003` |
| **Ingress** | `13-ingress.yaml` | Ingress | NGINX ingress routing `/` to `api-gateway:8003` |
| **Kustomization** | `kustomization.yaml` | Kustomization | Orchestrates all manifests in proper sequence |

---

## 🚀 Quickstart Guide (Local Minikube)

### 1. Prerequisites
Ensure you have the following installed on your host:
- [Docker](https://docs.docker.com/engine/install/)
- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)

### 2. Start Minikube
Allocate at least 4 CPUs and 4GB-8GB RAM:
```bash
minikube start --cpus=4 --memory=8192 --driver=docker
```

*(Optional)* Enable the Ingress addon if you wish to use Ingress:
```bash
minikube addons enable ingress
```

### 3. Build Docker Images Directly in Minikube
Run the automated image build script:
```bash
./k8s/build-images.sh
```
> **How this works**: If Minikube is active, `build-images.sh` automatically evaluates `eval $(minikube docker-env)`, building images directly inside Minikube's Docker daemon. No remote image push/pull is needed!

Verify that the images are in Minikube:
```bash
minikube image list | grep ecommerce
```

### 4. Deploy the Stack with Kustomize
Deploy all resources in one command:
```bash
kubectl apply -k k8s/
```

### 5. Monitor Deployment Status
Check until all Pods transition to `Running`:
```bash
kubectl get pods -n ecommerce -w
```

Example expected output:
```
NAME                                   READY   STATUS    RESTARTS   AGE
api-gateway-7b89785c4f-abcde           1/1     Running   0          45s
auth-service-67dbb54c87-fghij          1/1     Running   0          45s
notification-service-5c6d9bf79b-klmno  1/1     Running   0          45s
order-service-75b48bc57f-pqrst         1/1     Running   0          45s
payment-service-5f65dbfc6f-uvwxy       1/1     Running   0          45s
postgres-68894df876-z1234              1/1     Running   0          45s
product-service-6759c8bd9f-56789       1/1     Running   0          45s
rabbitmq-7cb46f97b-90123               1/1     Running   0          45s
```

Check Persistent Volumes and Services:
```bash
kubectl get pvc,svc,ingress -n ecommerce
```

---

## 🌐 Accessing the Application

### Method 1: Using Minikube Service URL (Recommended)
Open a terminal and run:
```bash
minikube service api-gateway -n ecommerce --url
```
This prints the local URL to reach the API Gateway (e.g., `http://192.168.49.2:30003` or `http://127.0.0.1:<random-port>`).

### Method 2: Port-Forward to Localhost
Port-forward directly from the cluster to `http://localhost:8003`:
```bash
kubectl port-forward svc/api-gateway -n ecommerce 8003:8003
```
Now you can send all API calls to `http://localhost:8003/api/...`.

To access the RabbitMQ Management dashboard:
```bash
kubectl port-forward svc/rabbitmq -n ecommerce 15672:15672
```
Open `http://localhost:15672` (Username: `guest`, Password: `guest`).

### Method 3: Ingress & Minikube Tunnel
If you enabled Ingress (`minikube addons enable ingress`), start the tunnel:
```bash
minikube tunnel
```
Now send requests to `http://localhost/api/...`.

---

## 🧪 Testing the Microservices Flow

You can test the full lifecycle using `curl` or Postman:

### 1. Register a User
```bash
curl -X POST http://localhost:8003/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "k8s_user",
    "email": "k8s@example.com",
    "password": "Password123!"
  }'
```

### 2. Login to Obtain Access Token
```bash
curl -X POST http://localhost:8003/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "k8s_user",
    "password": "Password123!"
  }'
```
*Copy the `access` token returned in the JSON response.*

### 3. Create a Product
```bash
curl -X POST http://localhost:8003/api/products/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -d '{
    "name": "Kubernetes Cloud Server",
    "description": "High availability k8s node cluster",
    "price": "99.99",
    "stock": 50
  }'
```

### 4. List Products
```bash
curl -X GET http://localhost:8003/api/products/ \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

### 5. Create an Order
```bash
curl -X POST http://localhost:8003/api/orders/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -d '{
    "items": [
      {
        "product_id": 1,
        "quantity": 2
      }
    ]
  }'
```
> **End-to-End Cascade**:
> 1. API Gateway verifies JWT RSA signature via Auth JWKS.
> 2. API Gateway proxies request to `order-service`.
> 3. Order Service contacts `product-service` via HTTP to verify stock and price.
> 4. Order Service contacts `payment-service` via **gRPC** (`payment-service:50051`).
> 5. Payment Service completes payment and publishes `order_notification` event to **RabbitMQ**.
> 6. `notification-service` consumes event from RabbitMQ and simulates sending an email!

Check notification worker logs:
```bash
kubectl logs -n ecommerce -l app=notification-service --tail=50
```

---

## 🛠 Useful Operations & Debugging

| Goal | Command |
| :--- | :--- |
| View logs of a service | `kubectl logs -n ecommerce -l app=api-gateway -f` |
| View logs of Order service | `kubectl logs -n ecommerce -l app=order-service -f` |
| Inspect Pod description / events | `kubectl describe pod <pod-name> -n ecommerce` |
| Run shell in PostgreSQL | `kubectl exec -it deployment/postgres -n ecommerce -- psql -U postgres` |
| Run Django migrations manually | `kubectl exec -it deployment/order-service -n ecommerce -- python manage.py migrate` |
| Re-render Kustomize YAML | `kubectl kustomize k8s/` |

---

## 🧹 Teardown

To delete all Kubernetes resources created by this stack:
```bash
kubectl delete -k k8s/
```

To stop Minikube:
```bash
minikube stop
```
