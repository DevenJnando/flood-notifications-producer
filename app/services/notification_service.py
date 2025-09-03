from app.dbschema.schema import Subscriber
from app.models.objects.flood_notification import FloodNotification
from app.models.objects.floods_with_postcodes import FloodWithPostcodes
from app.notifications.producer import Producer

from app.cache.flood_updates_cache import (flood_subscribers_are_cached,
                                           get_flood_subscribers_set,
                                           cache_flood_subscribers,
                                           severity_has_changed)
from app.logging.log import get_logger
from app.services.subscriber_service import get_all_subscribers_by_postcodes
from app.connections.database_orm import get_session


def return_relevant_subscribers(flood_with_postcodes: FloodWithPostcodes, subscribers: set[Subscriber]) -> set[Subscriber]:
    """
    Checks if a flood severity has changed in the redis database. If it has, the whole list of subscribers are returned
    since it is now treated as a new warning.

    If the warning has not changed, any subscribers not currently cached will be returned since they will be
    new subscribers who have not yet received a warning.
    @param flood_with_postcodes: FloodWithPostcodes object containing the FloodWarning pydantic model.
    @param subscribers: set of Subscriber objects.
    @return: set of Subscriber objects who need to be sent a notification.
    """
    if severity_has_changed(flood_with_postcodes.flood.floodAreaID,
                            flood_with_postcodes.flood.severityLevel,
                            flood_with_postcodes.flood.severity):
        return subscribers

    subscribers_dict: dict[str, Subscriber] = dict()
    subscriber_ids: set = set([str(x.id) for x in subscribers])
    subscribers_to_notifiy: set[Subscriber] = set()
    for subscriber in subscribers:
        subscribers_dict[str(subscriber.id)] = subscriber

    if flood_subscribers_are_cached(flood_with_postcodes.flood.floodAreaID, ):
        cached_subscriber_ids = get_flood_subscribers_set(flood_with_postcodes.flood.floodAreaID)
        subscriber_ids = subscriber_ids - cached_subscriber_ids
    if len(subscriber_ids) > 0:
        cache_flood_subscribers(flood_with_postcodes.flood.floodAreaID, subscriber_ids)

    for subscriber_id in subscriber_ids:
        if subscribers_dict.get(str(subscriber_id)):
            subscribers_to_notifiy.add(subscribers_dict.get(str(subscriber_id)))
    return subscribers_to_notifiy



def notify_subscribers(floods_with_postcodes: list[FloodWithPostcodes]) -> list[FloodNotification]:
    """
    Notifies all subscribers whose postcodes intersect with any given flood.

    @param floods_with_postcodes: a list of FloodWithPostcodes objects
    @return: a list of FloodNotifications objects which contain the relevant flood details and all affected subscribers
    @throws AttributeError: thrown if the producer context manager fails to send a notification
    """
    total_tasks = 0
    notifications: list[FloodNotification] = list()
    for flood_with_postcodes in floods_with_postcodes:
        subscribers: set[Subscriber] = set(get_all_subscribers_by_postcodes(get_session(), flood_with_postcodes.postcode_set))
        subscribers = set([x for x in subscribers if x is not None])
        subscribers = return_relevant_subscribers(flood_with_postcodes, subscribers)
        if len(subscribers) > 0:
            notification: FloodNotification = FloodNotification(flood_with_postcodes.flood, subscribers)
            total_tasks += len(subscribers)
            notifications.append(notification)
    with Producer(total_tasks) as producer:
        try:
            producer.notify_subscribers_by_email(notifications)
            producer.prepare_consumers()
        except AttributeError as e:
            get_logger(__name__).error(f"Failed to notify subscribers (Likely because the connection to rabbitmq failed): {e}")
            raise e
    return notifications