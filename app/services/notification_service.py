from app.dbschema.schema import Subscriber
from app.models.objects.flood_notification import FloodNotification
from app.models.objects.floods_with_postcodes import FloodWithPostcodes

from app.services.subscriber_service import get_all_subscribers_by_postcodes
from app.connections.database_orm import get_session


def gather_subscribers_to_be_notified(floods_with_postcodes: list[FloodWithPostcodes]) -> list[FloodNotification]:
    notifications: list[FloodNotification] = []
    for flood_with_postcode in floods_with_postcodes:
        subscribers: list[Subscriber] = get_all_subscribers_by_postcodes(get_session(), flood_with_postcode.postcode_set)
        subscribers = [x for x in subscribers if x is not None]
        notification: FloodNotification = FloodNotification(flood_with_postcode.flood, subscribers)
        notifications.append(notification)
    return notifications