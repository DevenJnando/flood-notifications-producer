import logging

from app.dbschema.schema import Subscriber
from app.models.objects.flood_notification import FloodNotification
from app.models.objects.floods_with_postcodes import FloodWithPostcodes
from app.notifications.producer import Producer

from app.services.subscriber_service import get_all_subscribers_by_postcodes
from app.connections.database_orm import get_session


logger = logging.getLogger(__name__)


def notify_subscribers(floods_with_postcodes: list[FloodWithPostcodes]) -> list[FloodNotification]:
    """
    Notifies all subscribers whose postcodes intersect with any given flood.

    @param floods_with_postcodes: a list of FloodWithPostcodes objects
    @return: a list of FloodNotifications objects which contain the relevant flood details and all affected subscribers
    @throws AttributeError: thrown if the producer context manager fails to send a notification
    """
    total_tasks = 0
    notifications: list[FloodNotification] = []
    for flood_with_postcode in floods_with_postcodes:
        subscribers: list[Subscriber] = get_all_subscribers_by_postcodes(get_session(), flood_with_postcode.postcode_set)
        subscribers = [x for x in subscribers if x is not None]
        notification: FloodNotification = FloodNotification(flood_with_postcode.flood, subscribers)
        total_tasks += len(subscribers)
        notifications.append(notification)
    with Producer(total_tasks) as producer:
        try:
            producer.notify_subscribers_by_email(notifications)
            producer.prepare_consumers()
        except AttributeError as e:
            logger.error(f"Failed to notify subscribers (Likely because the connection to rabbitmq failed): {e}")
            raise e
    return notifications