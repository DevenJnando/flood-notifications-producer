import logging
from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from email_validator import validate_email, EmailNotValidError, ValidatedEmail

from app.dbschema.schema import Subscriber, Postcode
from app.models.pydantic_models.subscriber_form import SubscriberForm


logger = logging.getLogger(__name__)


def get_all_subscribers(session: sessionmaker) -> list[Subscriber | None]:
    subscribers: list[Subscriber] = []
    subscriber_objects: list[Subscriber] = []
    with session() as session:
        query = select(Subscriber.id, Subscriber.email)
        subscribers = session.execute(query).all()
    for subscriber in subscribers:
        subscriber_object = Subscriber(id=subscriber.id, email=subscriber.email)
        subscriber_objects.append(subscriber_object)
    return subscriber_objects


def get_subscriber_by_id(session: sessionmaker, subscriber_id: UUID) -> Subscriber | None:
    with session() as session:
        subscriber: Subscriber | None = session.get(Subscriber, subscriber_id)
        if subscriber is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail=f"Subscriber with given id {subscriber_id} not found")
        return subscriber


def get_subscriber_by_email(session: sessionmaker, subscriber_email: str) -> Subscriber | None:
    with session() as session:
        subscriber: Subscriber | None = session.query(Subscriber).filter_by(email=subscriber_email).scalar()
        if subscriber is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail=f"Subscriber with given email {subscriber_email} not found")
        return subscriber


def get_subscribers_by_postcode(session: sessionmaker, postcode: str) -> list[Subscriber] | None:
    subscribers_with_postcode: list[Subscriber] = []
    with session() as session:
        statement = (select(Subscriber, Postcode)
                     .join(Subscriber.postcodes)
                     .order_by(Subscriber.id, Postcode.id)
                     .where(Postcode.postcode == postcode))
        for result in session.execute(statement):
            subscribers_with_postcode.append(result.Subscriber)
    if len(subscribers_with_postcode) == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"No subscribers with postcode {postcode} found in database.")
    return subscribers_with_postcode


def get_all_subscribers_by_postcodes(session: sessionmaker, postcodes: set[str]) -> list[Subscriber | None]:
    subscribers_with_postcodes: list[Subscriber] = []
    with session() as session:
        statement = (select(Subscriber, Postcode)
                     .join(Subscriber.postcodes)
                     .order_by(Subscriber.id, Postcode.id)
                     .where(Postcode.postcode.in_(postcodes)))
        for result in session.execute(statement):
            subscribers_with_postcodes.append(result.Subscriber)
    if len(subscribers_with_postcodes) == 0:
        logger.warning(f"No subscribers with postcodes {postcodes} found in database.")
    return subscribers_with_postcodes


def add_new_subscriber(session: sessionmaker, subscriber_form: SubscriberForm) -> None:
    try:
        with session() as session:
            subscriber_email: ValidatedEmail = validate_email(subscriber_form.email, check_deliverability=False)
            normalized_email: str = subscriber_email.normalized
            exists: bool = session.query(Subscriber).filter_by(email=normalized_email).scalar() is not None
            if exists:
                raise HTTPException(status_code=HTTPStatus.CONFLICT,
                                    detail=f"Subscriber with given email {subscriber_email} already exists")
            subscriber = Subscriber(email=normalized_email)
            for postcode in subscriber_form.postcodes:
                postcode_object = Postcode(postcode=postcode)
                subscriber.postcodes.append(postcode_object)
            session.add(subscriber)
            session.commit()
    except EmailNotValidError:
        raise HTTPException(status_code=HTTPStatus.NOT_ACCEPTABLE,
                            detail="The entered email {} is invalid".format(subscriber_form.email)
                            )


def delete_subscriber_by_id(session: sessionmaker, subscriber_id: UUID) -> None:
    with session() as session:
        subscriber: Subscriber | None = session.query(Subscriber).filter_by(id=subscriber_id).scalar()
        if subscriber is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail=f"Could not delete subscriber with id '{subscriber_id}' "
                                       f"because no such subscriber exists in the database.")
        statement = (select(Subscriber, Postcode)
                     .join(Subscriber.postcodes)
                     .order_by(Subscriber.id, Postcode.id)
                     .where(Subscriber.id == subscriber_id))
        for result in session.execute(statement):
            session.delete(result.Postcode)
        session.delete(subscriber)
        session.commit()


def delete_subscriber_by_email(session: sessionmaker, subscriber_email: str) -> None:
    with session() as session:
        subscriber: Subscriber | None = session.query(Subscriber).filter_by(email=subscriber_email).scalar()
        if subscriber is None:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                                detail=f"Could not delete subscriber with email '{subscriber_email}' "
                                       f"because no such subscriber exists in the database.")
        statement = (select(Subscriber, Postcode)
                     .join(Subscriber.postcodes)
                     .order_by(Subscriber.id, Postcode.id)
                     .where(Subscriber.id == subscriber.id))
        for result in session.execute(statement):
            session.delete(result.Postcode)
        session.delete(subscriber)
        session.commit()

