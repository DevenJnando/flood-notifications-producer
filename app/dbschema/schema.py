from typing import List
from uuid import UUID, uuid4

from sqlalchemy import String, ForeignKey
from sqlalchemy.schema import FetchedValue
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from app.dbschema.base import Base


class Subscriber(Base):
    __tablename__ = "subscribers"
    id: Mapped[UUID] = mapped_column(default=uuid4, server_default=FetchedValue(), primary_key=True)
    email: Mapped[str] = mapped_column(String(30))
    postcodes: Mapped[List["Postcode"]] = relationship(back_populates="subscriber")
    def __repr__(self) -> str:
        return f"Subscriber(id={self.id!r}, name={self.email!r})"

class Postcode(Base):
    __tablename__ = "postcodes"
    id: Mapped[UUID] = mapped_column(default=uuid4, server_default=FetchedValue(), primary_key=True)
    postcode: Mapped[str] = mapped_column(String(8))
    subscriber_id: Mapped[UUID] = mapped_column(ForeignKey("subscribers.id"))
    subscriber: Mapped[Subscriber] = relationship(back_populates="postcodes")
    def __repr__(self) -> str:
        return f"Address(id={self.id!r}, postcode={self.postcode!r})"