from pydantic import BaseModel


class Power(BaseModel):
    name: str
    level: int
    raw: str
    percent: float
    value: float
    plus: int


class sp_prop(BaseModel):
    dmgBonus: float = 0
    addDmg: float = 0
    attack: float = 0
