import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
print("path --> ", BASE_DIR)
sys.path.append(str(BASE_DIR / "protos"))

import grpc
import payment_pb2
import payment_pb2_grpc

channel = grpc.insecure_channel("localhost:50051")

stub = payment_pb2_grpc.PaymentServiceStub(channel)


def PaymentTransaction(user_id, order_id, amount):

    req = payment_pb2.PaymentRequest(user_id=user_id, order_id=order_id, amount=amount)

    response = stub.ProcessPayment(req)

    print(response.success, response.transaction_id)

    return response
