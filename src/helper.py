from database import Tower


def create_tower():
    tower = Tower()
    tower.health = 5000
    tower.defense = 0
    tower.defender_count = 0
    tower.session = 0
    return create_tower
