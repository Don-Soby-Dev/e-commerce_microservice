import json
import pika


def publish_payment_success_even(order_id, user_id, amount):

    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))

    channel = connection.channel()

    queue_name = "order_notification"
    channel.queue_declare(queue=queue_name, durable=True)

    message = {
        "event": "PAYMENT_CONFIRMED",
        "order_id": order_id,
        "user_id": user_id,
        "amount": amount,
    }

    channel.basic_publish(
        exchange="",
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(delivery_mode=2),
    )

    print(f"[x] Sent event: {message}")

    connection.close()
