import os
import unittest
import json
import pika
from pika.exceptions import AMQPConnectionError, NackError

from app.dbschema.schema import Subscriber
from app.models.objects.flood_notification import FloodNotification
from app.models.objects.floods_with_postcodes import FloodWithPostcodes
from app.models.pydantic_models.flood_warning import FloodWarning
from app.notifications.producer import Producer
from app.services.notification_service import notify_subscribers

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

try:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
except AMQPConnectionError:
    connection = None

class NotificationTests(unittest.TestCase):


    def test_producer(self):
        no_of_tasks: int = 1000
        flood_key: str = "flood"
        subscriber_email_key: str = "subscriber_email"
        flood_area_id_key: str = "floodAreaID"
        flood_description_key: str = "description"
        flood_severity_key: str = "severity"
        flood_severity_level_key: str = "severityLevel"
        flood_message_key: str = "message"
        test_notification: dict = {
            flood_key: {
                flood_area_id_key: "floodAreaID",
                flood_description_key: "description",
                flood_severity_key: "severity",
                flood_severity_level_key: 1,
                flood_message_key: "message"
            },
            subscriber_email_key: "subscriberEmail"
        }
        try:
            with Producer(no_of_tasks) as producer:
                for i in range(no_of_tasks):
                    producer.publish(body=json.dumps(test_notification), routing_key='email')
                producer.prepare_consumers()
        except (AMQPConnectionError, AttributeError, NackError) as e:
            self.fail(f"Encountered a producer exception: {e}")


    def test_gather_subscribers(self):
        if connection is None:
            self.fail("Cannot publish to producer because rabbitmq is not available. "
                          "Make sure rabbitmq is running on the correct port, and re-run tests.")
        test_floods: list[dict] = json.loads(open(root_dir + "/fixtures/test_floods.json").read()).get("items")
        test_floods_as_objects: list[FloodWarning] = [FloodWarning(**flood) for flood in test_floods]
        test_postcodes: list[dict] = json.loads(open(root_dir + "/fixtures/test_floods_postcodes.json").read())
        test_postcodes_as_objects: list[FloodWithPostcodes] = []
        for test_flood in test_floods_as_objects:
            for test_postcode in test_postcodes:
                if test_postcode.get("floodID") == test_flood.floodAreaID:
                    test_postcodes_as_objects.append(
                        FloodWithPostcodes(test_flood, test_postcode.get("postcodesInRange")))
        notifications_to_send: list[FloodNotification] = (
            notify_subscribers(test_postcodes_as_objects))
        assert len(notifications_to_send) > 0
        for notification in notifications_to_send:
            assert isinstance(notification, FloodNotification)
            for subscriber in notification.subscribers:
                assert isinstance(subscriber, Subscriber)


if __name__ == '__main__':
    unittest.main()