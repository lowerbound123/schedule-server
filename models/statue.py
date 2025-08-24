from . import Carrier, Shelf, Machine
from pydantic import BaseModel

class Statue(BaseModel):
    carriers: dict[str, Carrier]
    shelves: dict[str, Shelf]
    machines: dict[str, Machine]
    distance: dict[str, int]