from pydantic import BaseModel


class GDPRDeleteOut(BaseModel):
    deleted: bool
    hashed_reference: str
    message: str
