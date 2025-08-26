import json
import sys
from uuid import UUID

import pika
import logging

from pika.exceptions import AMQPConnectionError, NackError
from app.models.objects.flood_notification import FloodNotification

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)


class Producer:
    """
    Producer object which establishes a connection to RabbitMQ and prepares any notifications
    to be accepted by the consumer. This includes any notification email notifications to be sent,
    as well as the total number of emails for the task manager queue.
    """

    def __init__(self, no_of_tasks: int):
        self.logger = logging.getLogger(__name__)
        self.dead_letter_log = logging.getLogger('dead_letter_log')
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            self.channel = self.connection.channel()
            self.channel.confirm_delivery()
            self.channel.queue_declare(queue='tasks', durable=True, arguments={"x-queue-type": "quorum"})
            self.channel.queue_declare(queue='email', durable=True, arguments={"x-queue-type": "quorum"})
            self.task_key = "no_of_tasks"
            self.flood_key = "flood"
            self.subscriber_id_key = "subscriber_id"
            self.subscriber_email_key = "subscriber_email"
            self.serialized_no_of_tasks: str = json.dumps(
                {
                    self.task_key: no_of_tasks
                }
            )
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


    def publish(self, body: str, routing_key: str, attempt: int = 0):
        """
        Publishes a message to RabbitMQ.

        @param body: the body of the message to be sent
        @param routing_key: the queue for the message to be placed onto
        @param attempt: the current attempt number. If left blank, it defaults to 0.
        """
        ATTEMPT_LIMIT = 5
        try:
            self.channel.basic_publish(exchange='', routing_key=routing_key, body=body,
                                       mandatory=True)
        except NackError:
            if attempt < ATTEMPT_LIMIT:
                attempt += 1
                self.publish(body, routing_key, attempt)
                self.logger.warning(f"Failed to publish notification. Retrying (attempt {attempt} of {ATTEMPT_LIMIT})")
            else:
                self.logger.error(f"Maximum number of re-attempts exceeded.")
                self.dead_letter_log.error(f"Maximum number of re-attempts exceeded for \n"
                                           f"{body}")


    def prepare_consumers(self):
        """
        Sends the total number of emails to the task manager queue.
        """
        self.publish(body=self.serialized_no_of_tasks, routing_key='tasks')


    def notify_subscribers_by_email(self, flood_notifications: list[FloodNotification]) -> None:
        """
        Creates a message with the given flood ID, the suscriber ID and the subscriber email address
        for each subscriber in a list of FloodNotification objects.

        @param flood_notifications: a list of FloodNotification objects
        """
        for notification in flood_notifications:
            for subscriber in notification.subscribers:
                serializable_flood: dict = notification.flood.model_dump()
                serializable_subscriber_id: str = str(subscriber.id)
                serializable_subscriber_email: str = subscriber.email
                serialized_flood_notification: str = json.dumps(
                    {
                        self.flood_key: serializable_flood,
                        self.subscriber_id_key: serializable_subscriber_id,
                        self.subscriber_email_key: serializable_subscriber_email
                    }
                )
                self.publish(body=serialized_flood_notification, routing_key='email')
