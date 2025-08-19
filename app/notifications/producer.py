import json
import sys

import pika
import logging

from pika.exceptions import AMQPConnectionError, NackError
from app.models.objects.flood_notification import FloodNotification


class Producer:

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.dead_letter_log = logging.getLogger('dead_letter_log')
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            self.channel = self.connection.channel()
            self.channel.confirm_delivery()
            self.channel.queue_declare(queue='email', durable=True, arguments={"x-queue-type": "quorum"})
            self.flood_key = "flood"
            self.subscriber_email_key = "subscriber_email"
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


    def publish(self, body: str, attempt: int = 0):
        ATTEMPT_LIMIT = 5
        try:
            self.channel.basic_publish(exchange='', routing_key='email', body=body,
                                       mandatory=True)
        except NackError:
            if attempt < ATTEMPT_LIMIT:
                attempt += 1
                self.publish(body, attempt)
                self.logger.warning(f"Failed to publish notification. Retrying (attempt {attempt} of {ATTEMPT_LIMIT})")
            else:
                self.logger.error(f"Maximum number of re-attempts exceeded.")
                self.dead_letter_log.error(f"Maximum number of re-attempts exceeded for \n"
                                           f"{body}")


    def notify_subscribers_by_email(self, flood_notifications: list[FloodNotification]) -> None:
        for notification in flood_notifications:
            for subscriber in notification.subscribers:
                serializable_flood: dict = notification.flood.model_dump()
                serializable_subscriber: str = subscriber.email
                serialized_flood_notification: str = json.dumps(
                    {
                        self.flood_key: serializable_flood,
                        self.subscriber_email_key: serializable_subscriber
                    }
                )
                self.publish(body=serialized_flood_notification)
