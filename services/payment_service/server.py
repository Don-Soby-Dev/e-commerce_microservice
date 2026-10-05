from concurrent import futures
import grpc
import uuid
import os

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
for p in [str(BASE_DIR / "protos"), "/protos"]:
    if p not in sys.path:
        sys.path.append(p)

import payment_pb2  # pyright: ignore[reportMissingImports]
import payment_pb2_grpc  # pyright: ignore[reportMissingImports]
from producer import publish_payment_success_event


class PaymentServicer(payment_pb2_grpc.PaymentServiceServicer):

    def ProcessPayment(self, request, context):

        print(
            f"Processing payment for Order #{request.order_id}, Amount: ${request.amount}"
        )

        if request.amount <= 0:
            return payment_pb2.PaymentResponse(
                success=False, transaction_id="", message="Invalid amount"
            )

        tx_id = f"tx_{uuid.uuid4().hex[:10]}"
        publish_payment_success_event(
            request.order_id,
            request.user_id,
            request.amount,
        )
        return payment_pb2.PaymentResponse(
            success=True, transaction_id=tx_id, message=""
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(PaymentServicer(), server)
    bind_address = os.getenv("GRPC_BIND_ADDR", "0.0.0.0:50051")
    server.add_insecure_port(bind_address)
    print(f"gRPC payment Service running on port {bind_address}...")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
