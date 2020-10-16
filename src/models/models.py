from pydantic import BaseModel


class Nickname(BaseModel):
    nickname: str


class Message(BaseModel):
    message: str = ''
    tower: str = ''
    sender: str = ''
    health: int = 0
    shield: int = 0


class Item(BaseModel):
    towerName: str = None

    towerHealth: int = None
    towerDefense: int = None

    towerDefenders: int = None
    enemyTowerDefenders: int = None

    serverUri: str = None
    enemyTowerHealth: int = None
    enemyTowerName: str = None


class Towermodel:
    health: int
    defense: int
    session: int
    defender_count: int


class Defender:
    nickname: str
    attack_points_generated: int
    defense_points_generated: int
    tower: str


class Session:
    session_id: int
    time_created: str
    global_defender_count: int
    hocus_tower: int
    pocus_towe: int


class UserStatistics:
    attack_points_generated: int
    defense_points_generated: int
