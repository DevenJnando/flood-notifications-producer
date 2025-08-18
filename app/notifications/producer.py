import json
import sys

import pika
import logging

from pika.exceptions import AMQPConnectionError
from app.models.objects.flood_notification import FloodNotification


class Producer:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue='email', durable=True)
            self.flood_key = "flood"
            self.subscriber_emails_key = "subscriber_emails"
        except AMQPConnectionError as e:
            self.logger.error("Could not connect to rabbitmq. Ensure rabbitmq is running.\n"
                              f"AMQPConnectionError: {e}")
            self.__exit__(*sys.exc_info())
            raise e

    def __enter__(self):
        return self


    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.connection.close()
        except AttributeError as e:
            self.logger.warning("Did not close connection to rabbitmq because "
                                "no connection field had been initialised (Check that rabbitmq is running).")
            raise e


    def notify_subscribers_by_email(self, flood_notifications: list[FloodNotification]) -> None:
        for notification in flood_notifications:
            serializable_flood: dict = notification.flood.model_dump()
            serializable_subscriber_list: list[str] = [subscriber.email for subscriber in notification.subscribers]
            serialized_flood_notification: str = json.dumps(
                {
                    self.flood_key: serializable_flood,
                    self.subscriber_emails_key: serializable_subscriber_list
                }
            )
            self.channel.basic_publish(exchange='', routing_key='email', body=serialized_flood_notification)