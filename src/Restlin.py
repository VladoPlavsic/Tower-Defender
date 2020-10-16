import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sender import sender
from receiver import amqp__ini__
from random import randint
from database import Database
from models.models import Item, Nickname, Defender, UserStatistics, Message, Towermodel
import requests
import json
import threading
import logging
import sys


SESSION_ID = 0
HOCUS = "localhost:666"
POCUS = "localhost:999"
MESSAGE = {'message': '', 'Hocus': '',
           'Pocus': '', 'Hocus Defenders': '', 'Pocus Defenders': ''}

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"]
)


def chose():
    db = Database()
    h = db.get_defender_count("Hocus", SESSION_ID)
    p = db.get_defender_count("Pocus", SESSION_ID)
    if h > p:
        return POCUS
    else:
        return HOCUS

# Hocus port 666, Pocus port 999


def create_response(db, tower):
    rs = db.get_tower_statistics(tower, SESSION_ID)

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


@app.post("/user")
def create_user(nickname: Nickname):
    user = create_user_from_nick(nickname.nickname, chose())
    db = Database()
    created = db.create_user(user)
    response = create_response(db, user.tower)
    if(not created):
        response.towerName = "Error"
    return response


@app.get('/defender')
def get_user_statistics(nickname: Nickname):
    db = Database()
    statistics = db.get_user_statistics(nickname)
    return statistics


@app.get('/tower')
def get_tower_data(tower: Nickname):
    '''get_tower_data(tower: Hocus or Pocus) -> tower statistics : Item'''
    db = Database()
    statistics = db.get_tower_statistics(tower.nickname, SESSION_ID)
    data = Message()
    data.shield = statistics.towerDefense
    data.health = statistics.towerHealth
    return data


@app.put("/defender")
def update_defender(message: Message):
    print("*******************")
    print("UPDATE DEFENDER CALLED")
    print("*******************")
    db = Database()
    updated = update_defender_help(db, message)
    db.update_user(message.sender, updated)
    if(message.message == "shield"):
        db.update_tower_defense(SESSION_ID, -100, message.tower)


def update_defender_help(db, message):
    statistics = db.get_user_statistics(message.sender)

    if(message.message == "attack"):
        statistics.attack_points_generated += 100
    elif(message.message == "shield"):
        statistics.defense_points_generated += 150
    return statistics


@app.put("/tower")
def update_tower(message: Message):
    print("*******************")
    print(
        f"UPDATE TOWER CALLED WITH MESSAGE {message.message}\nHEALTH {message.health} AND SHIELD {message.shield}")
    print("*******************")
    db = Database()
    if(message.message == "health_attacked" or message == "shield"):
        if(message.message == "health_attacked"):
            db.update_tower_health(SESSION_ID, message.health, message.tower)
        db.update_tower_defense(SESSION_ID, message.shield, message.tower)
    else:
        updated = update_tower_help(db, message)
        db.update_tower(SESSION_ID, updated)
        MESSAGE["message"] = message.message
        MESSAGE[updated.towerName] = updated.towerHealth
        MESSAGE[updated.enemyTowerName] = updated.enemyTowerHealth
        MESSAGE[updated.towerName + ' Defenders'] = updated.towerDefenders
        MESSAGE[updated.enemyTowerName +
                ' Defenders'] = updated.enemyTowerDefenders
        sender._send(MESSAGE, ["Hocus", "Pocus"])


def update_tower_help(db, message):
    statistics = db.get_tower_statistics(message.tower, SESSION_ID)
    if(message.message == "connect"):
        statistics.towerHealth += 1000
        statistics.enemyTowerHealth += 1000
        statistics.towerDefenders += 1
    elif(message.message == "disconnect"):
        if(statistics.towerHealth > 500):
            statistics.towerHealth -= 500
        statistics.towerDefenders -= 1
    return statistics


def start_amqp():

    print(f"Started amqp")

    def amqp_callback(ch, method, properties, body):
        message = json.loads(body)["message"]
        print("*******************")
        print(f"DATA RECEIVED WITH MESSAGE {message}")
        print("*******************")
        if(message == "connect" or message == "disconnect"):
            requests.put('http://localhost:1337/tower', data=body)
        if(message == "attack" or message == "shield"):
            requests.put('http://localhost:1337/defender', data=body)

    amqp__ini__(routing_key="Restlin", amqp_callback=amqp_callback)


def start_unicorn():
    uvicorn.run(app, host="localhost", port=1337)


if __name__ == "__main__":
    db = Database()
    SESSION_ID = db.create_session()
    amqp = threading.Thread(target=start_amqp)
    amqp.start()
    start_unicorn()
