from database import Database
from models.models import Defender
import uvicorn
import json
import requests
from receiver import amqp__ini__
from logger.logger import Logger

HOCUS = "localhost:666"
POCUS = "localhost:999"

logger = Logger(filename="restlin.log")


def chose(session_id):
    db = Database()
    h = db.get_defender_count(tower="Hocus", session_id=session_id)
    p = db.get_defender_count(tower="Pocus", session_id=session_id)
    if h > p:
        return POCUS
    else:
        return HOCUS


def create_response(db, tower, session_id):
    rs = db.get_tower_statistics(tower, session_id)

    rs.towerHealth += 1000
    rs.towerDefenders += 1
    rs.enemyTowerHealth += 1000
    return rs


def create_user_from_nick(nickname: str, tower: str):
    user = Defender()
    user.nickname = nickname
    user.attack_points_generated = 0
    user.defense_points_generated = 0
    if(tower == HOCUS):
        user.tower = "Hocus"
    else:
        user.tower = "Pocus"
    return user


def update_defender_help(db, message):
    statistics = db.get_user_statistics(message.sender)

    if(message.message == "attack"):
        statistics.attack_points_generated += 100
    elif(message.message == "shield"):
        statistics.defense_points_generated += 150
    return statistics


def update_tower_help(db, message, session_id):
    statistics = db.get_tower_statistics(message.tower, session_id)

    if(message.message == "connect"):
        statistics.towerHealth += 1000
        statistics.enemyTowerHealth += 1000
        statistics.towerDefenders += 1
    elif(message.message == "disconnect"):
        logger.log_info(
            f"UPDATE TOWER CALLED WITH HP {statistics.towerHealth} AND {statistics.towerDefense} AND WILL BE REMOVED 500 {message.message.upper()}")
        if(statistics.towerHealth > 500):
            statistics.towerHealth -= 500
        statistics.towerDefenders -= 1
    return statistics


def start_unicorn(app, host, port):
    uvicorn.run(app, host=host, port=port)


def start_amqp():

    print(f"Started amqp")

    def amqp_callback(ch, method, properties, body):
        message = json.loads(body)["message"]
        logger.log_info(f"DATA RECEIVED WITH MESSAGE {message}")

        if(message == "connect" or message == "disconnect"):
            requests.put('http://localhost:1337/tower', data=body)
        if(message == "attack" or message == "shield"):
            requests.put('http://localhost:1337/defender', data=body)

    amqp__ini__(routing_key="Restlin", amqp_callback=amqp_callback)
