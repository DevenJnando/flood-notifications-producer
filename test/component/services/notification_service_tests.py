import os
import unittest
import json

from app.dbschema.schema import Subscriber
from app.models.objects.flood_notification import FloodNotification
from app.models.objects.floods_with_postcodes import FloodWithPostcodes
from app.services.notification_service import gather_subscribers_to_be_notified

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))


class NotificationTests(unittest.TestCase):


    def test_gather_subscribers_mock_method(self):
        test_postcodes: list[dict] = json.loads(open(root_dir + "/fixtures/test_floods_postcodes.json").read())
        test_postcodes_as_objects: list[FloodWithPostcodes] = \
            [FloodWithPostcodes(postcode.get("floodID"), postcode.get("postcodesInRange"))
             for postcode in test_postcodes]
        notifications_to_send: list[FloodNotification] = (
            gather_subscribers_to_be_notified(test_postcodes_as_objects))
        assert len(notifications_to_send) > 0
        for notification in notifications_to_send:
            assert isinstance(notification, FloodNotification)
            for subscriber in notification.subscribers:
                assert isinstance(subscriber, Subscriber)


if __name__ == '__main__':
    unittest.main()