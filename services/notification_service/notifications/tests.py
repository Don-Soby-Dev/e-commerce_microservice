import json
from unittest.mock import MagicMock, patch
from django.test import TestCase

from .consumer import process_message


class NotificationConsumerTests(TestCase):
    def setUp(self):
        self.mock_channel = MagicMock()
        self.mock_method = MagicMock()
        self.mock_method.delivery_tag = 42

    @patch("notifications.consumer.time.sleep")
    def test_process_message_success(self, mock_sleep):
        payload = {
            "order_id": 100,
            "user_id": 1,
            "amount": 250,
            "status": "COMPLETED"
        }
        body = json.dumps(payload).encode("utf-8")

        process_message(self.mock_channel, self.mock_method, None, body)

        self.mock_channel.basic_ack.assert_called_once_with(delivery_tag=42)
        mock_sleep.assert_called_once_with(1)

    @patch("notifications.consumer.time.sleep")
    def test_process_message_partial_payload(self, mock_sleep):
        payload = {"user_id": 5}
        body = json.dumps(payload).encode("utf-8")

        process_message(self.mock_channel, self.mock_method, None, body)

        self.mock_channel.basic_ack.assert_called_once_with(delivery_tag=42)

    def test_process_message_invalid_json(self):
        body = b"not-a-valid-json"
        with self.assertRaises(json.JSONDecodeError):
            process_message(self.mock_channel, self.mock_method, None, body)
