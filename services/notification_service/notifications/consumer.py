import json
import time
import pika


def process_message(ch, methode, properties, body):

    data = json.loads(body)
    print(f" [x] Received notification task: {data}")

    user_id = data.get("user_id")
    amount = data.get("amount")
    print(f" 📧 Sending confirmation email to User #{user_id} for ${amount}...")
    time.sleep(1)  # Simulate email network latency
    print(" ✅ Email sent successfully!")

    ch.basic_ack(delivery_tag=methode.delivery_tag)


def start_counsumer():

    connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
    channel = connection.channel()

    queue_name = "order_notification"
    channel.queue_declare(queue=queue_name, durable=True)

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(queue=queue_name, on_message_callback=process_message)
    print(" [*] Notification Service is waiting for messages. To exit press CTRL+C")

    channel.start_consuming()


if __name__ == "__main__":
    start_counsumer()
