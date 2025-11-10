from pydantic import BaseModel
from typing import Dict


class Action(BaseModel):
    item: str
    quantity: int


class FactoryState(BaseModel):
    balance: float
    revenue: float
    inventory: Dict[str, int]
