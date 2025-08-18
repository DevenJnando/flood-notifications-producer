import os
import unittest
import json
from unittest.mock import patch

from sqlalchemy.engine.create import create_engine
from sqlalchemy.orm.session import sessionmaker

from app.dbschema.base import Base
from app.dbschema.schema import Subscriber, Postcode
from app.models.objects.flood_notification import FloodNotification
from app.models.objects.floods_with_postcodes import FloodWithPostcodes
from app.models.pydantic_models.flood_warning import FloodWarning
from app.services.subscriber_service import get_all_subscribers_by_postcodes

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

mailing_list_engine = create_engine("sqlite+pysqlite:///" + root_dir + "/mock-database/:testdb.db:", echo=True)
session = sessionmaker(mailing_list_engine, expire_on_commit=False)


def mock_gather_subscribers_to_be_notified(floods_with_postcodes: list[FloodWithPostcodes]) -> list[FloodNotification]:
    notifications: list[FloodNotification] = []
    for flood_with_postcode in floods_with_postcodes:
        subscribers: list[Subscriber] = get_all_subscribers_by_postcodes(session, flood_with_postcode.postcode_set)
        subscribers = [x for x in subscribers if x is not None]
        notification: FloodNotification = FloodNotification(flood_with_postcode.flood, subscribers)
        notifications.append(notification)
    return notifications


class NotificationTests(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(mailing_list_engine)
        with session() as current_session:
            subscriber1 = Subscriber(email="crenando_178ma@mailsac.com")
            subscriber2 = Subscriber(email="crenando_1mpb7@mailsac.com")
            subscriber3 = Subscriber(email="crenando_4qhqm@mailsac.com")
            subscriber4 = Subscriber(email="crenando_alq68@mailsac.com")
            subscriber5 = Subscriber(email="crenando_i4d9u@mailsac.com")
            subscriber6 = Subscriber(email="crenando_6xuwb@mailsac.com")
            subscriber7 = Subscriber(email="crenando_5umgc@mailsac.com")
            subscriber8 = Subscriber(email="crenando_zunj7@mailsac.com")
            subscriber9 = Subscriber(email="crenando_tk8ym@mailsac.com")
            subscriber10 = Subscriber(email="crenando_bmtj4@mailsac.com")

            postcode1 = Postcode(postcode="LA8 9LF", subscriber=subscriber1)
            postcode2 = Postcode(postcode="DL8 4RR", subscriber=subscriber2)
            postcode3 = Postcode(postcode="LA9 6HG", subscriber=subscriber4)
            postcode4 = Postcode(postcode="LA8 8JJ", subscriber=subscriber5)
            postcode5 = Postcode(postcode="LA12 8NS", subscriber=subscriber6)
            postcode6 = Postcode(postcode="LA22 9EA", subscriber=subscriber8)
            postcode7 = Postcode(postcode="LA22 9DG", subscriber=subscriber9)
            postcode8 = Postcode(postcode="LA22 0DY", subscriber=subscriber10)
            postcode9 = Postcode(postcode="LA8 9LF", subscriber=subscriber7)
            postcode10 = Postcode(postcode="DL8 4RR", subscriber=subscriber3)
            postcode11 = Postcode(postcode="LA12 8NS", subscriber=subscriber7)

            subscriber1.postcodes = [postcode1]
            subscriber2.postcodes = [postcode2]
            subscriber3.postcodes = [postcode10]
            subscriber4.postcodes = [postcode3]
            subscriber5.postcodes = [postcode4]
            subscriber6.postcodes = [postcode5]
            subscriber7.postcodes = [postcode1, postcode9, postcode11]
            subscriber8.postcodes = [postcode6]
            subscriber9.postcodes = [postcode7]
            subscriber10.postcodes = [postcode8]

            full_list = [subscriber1, subscriber2, subscriber3, subscriber4, subscriber5, subscriber6,
                         subscriber7, subscriber8, subscriber9, subscriber10,
                         postcode1, postcode2, postcode3, postcode4, postcode5, postcode6,
                         postcode7, postcode8, postcode9, postcode10, postcode11]
            current_session.add_all(full_list)
            current_session.commit()


    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(mailing_list_engine)


    @patch("app.services.notification_service.gather_subscribers_to_be_notified")
    def test_gather_subscribers_matches_mock_return_value(self, mock_gather_method):
        test_subscriber = Subscriber(email="testemail@testmail.com")
        test_postcode = Postcode(postcode="LA96HG", subscriber=test_subscriber)
        test_subscriber.postcodes.append(test_postcode)
        test_floods: list[dict] = json.loads(open(root_dir + "/fixtures/test_floods.json").read()).get("items")
        test_floods_as_objects: list[FloodWarning] = [FloodWarning(**flood) for flood in test_floods]
        test_notification = FloodNotification(test_floods_as_objects[0], [test_subscriber])
        mock_gather_method.return_value = [test_notification]
        test_postcodes: list[dict] = json.loads(open(root_dir + "/fixtures/test_floods_postcodes.json").read())
        test_postcodes_as_objects: list[FloodWithPostcodes] = []
        for test_flood in test_floods_as_objects:
            for test_postcode in test_postcodes:
                if test_postcode.get("floodID") == test_flood.floodAreaID:
                    test_postcodes_as_objects.append(
                        FloodWithPostcodes(test_flood, test_postcode.get("postcodesInRange")))
        assert mock_gather_method(test_postcodes_as_objects) == [test_notification]


    @patch("app.services.notification_service.gather_subscribers_to_be_notified")
    def test_gather_subscribers_no_matches_mock_return_value(self, mock_gather_method):
        mock_gather_method.return_value = []
        test_floods: list[dict] = json.loads(open(root_dir + "/fixtures/test_floods.json").read()).get("items")
        test_floods_as_objects: list[FloodWarning] = [FloodWarning(**flood) for flood in test_floods]
        test_postcodes: list[dict] = json.loads(open(root_dir + "/fixtures/test_floods_postcodes.json").read())
        test_postcodes_as_objects: list[FloodWithPostcodes] = []
        for test_flood in test_floods_as_objects:
            for test_postcode in test_postcodes:
                if test_postcode.get("floodID") == test_flood.floodAreaID:
                    test_postcodes_as_objects.append(
                        FloodWithPostcodes(test_flood, test_postcode.get("postcodesInRange")))
        assert mock_gather_method(test_postcodes_as_objects) == []


    @patch("app.services.notification_service.gather_subscribers_to_be_notified")
    def test_gather_subscribers_mock_method(self, mock_gather_method):
        mock_gather_method.side_effect = mock_gather_subscribers_to_be_notified
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
            mock_gather_method(test_postcodes_as_objects))
        assert len(notifications_to_send) > 0
        for notification in notifications_to_send:
            assert isinstance(notification, FloodNotification)
            for subscriber in notification.subscribers:
                assert isinstance(subscriber, Subscriber)


if __name__ == '__main__':
    unittest.main()