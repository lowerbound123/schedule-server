from pydantic import BaseModel

class StandardResponse(BaseModel):
    carrier: str
    orgi: str
    dest: str