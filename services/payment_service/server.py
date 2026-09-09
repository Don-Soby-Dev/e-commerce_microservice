from concurrent import futures
import grpc
import uuid

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
print(BASE_DIR)
sys.path.append(str(BASE_DIR / "protos"))

import payment_pb2
import payment_pb2_grpc


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
        return payment_pb2.PaymentResponse(
            success=True, transaction_id=tx_id, message=""
        )


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    payment_pb2_grpc.add_PymentServiceServicer_to_server(PaymentServicer(), server)
    server.add_insecure_port("[::]:50051")
    print("gRPC payment Service running on port 50051...")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
