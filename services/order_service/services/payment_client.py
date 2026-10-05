import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
for p in [str(BASE_DIR / "protos"), "/protos"]:
    if p not in sys.path:
        sys.path.append(p)

import grpc
import payment_pb2
import payment_pb2_grpc

import os

PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "localhost:50051")
channel = grpc.insecure_channel(PAYMENT_SERVICE_URL)

stub = payment_pb2_grpc.PaymentServiceStub(channel)


def PaymentTransaction(user_id, order_id, amount):

    req = payment_pb2.PaymentRequest(user_id=user_id, order_id=order_id, amount=amount)

    response = stub.ProcessPayment(req)

    print(response.success, response.transaction_id)

    return response
