from pydantic import BaseModel

class SubscriberForm(BaseModel):
    email: str
    postcodes: list[str]