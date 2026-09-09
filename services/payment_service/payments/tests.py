from django.test import TestCase
from unittest.mock import MagicMock
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))
if str(BASE_DIR / "protos") not in sys.path:
    sys.path.append(str(BASE_DIR / "protos"))

from protos import payment_pb2
from server import PaymentServicer


class PaymentServicerTestCase(TestCase):
    def setUp(self):
        self.servicer = PaymentServicer()
        self.context = MagicMock()

    def test_process_payment_success(self):
        request = payment_pb2.PaymentRequest(
            user_id=1,
            order_id=101,
            amount=5000,
        )
        response = self.servicer.ProcessPayment(request, self.context)

        self.assertTrue(response.success)
        self.assertTrue(response.transaction_id.startswith("tx_"))
        self.assertEqual(response.message, "Payment processed successfully")

    def test_process_payment_invalid_amount_zero(self):
        request = payment_pb2.PaymentRequest(
            user_id=1,
            order_id=102,
            amount=0,
        )
        response = self.servicer.ProcessPayment(request, self.context)

        self.assertFalse(response.success)
        self.assertEqual(response.transaction_id, "")
        self.assertEqual(response.message, "Invalid amount")

    def test_process_payment_invalid_amount_negative(self):
        request = payment_pb2.PaymentRequest(
            user_id=1,
            order_id=103,
            amount=-100,
        )
        response = self.servicer.ProcessPayment(request, self.context)

        self.assertFalse(response.success)
        self.assertEqual(response.transaction_id, "")
        self.assertEqual(response.message, "Invalid amount")
