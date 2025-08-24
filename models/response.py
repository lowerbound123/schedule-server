from pydantic import BaseModel

class StandardResponse(BaseModel):
    carrier: str | None
    orgi: str | None
    dest: str | None