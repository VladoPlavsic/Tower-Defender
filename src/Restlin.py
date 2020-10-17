import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sender import sender
from receiver import amqp__ini__
from database import Database
from models.models import Nickname, Defender, Message
import requests
import json
import threading
import logging
import sys
from restlin_helping_functions import HOCUS, POCUS, create_user_from_nick, chose, create_response, update_defender_help, update_tower_help, start_unicorn, start_amqp, logger

SESSION_ID = 0
HOST = 'localhost'
PORT = 1337
MESSAGE = {'message': '', 'Hocus': '',
           'Pocus': '', 'Hocus Defenders': '', 'Pocus Defenders': ''}

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# POST ROUTE FOR CREATING A USER
@app.post("/user")
def create_user(nickname: Nickname):
    '''
        NOTE: requests.post("http://localhost:1337/user", data=json.dumps({"nickname": "some_nickname"}))

        Nickname model:
        nickname: str
    '''

    user = create_user_from_nick(
        nickname.nickname, chose(session_id=SESSION_ID))
    db = Database()
    created = db.create_user(user)
    response = create_response(db, user.tower, SESSION_ID)
    if(not created):
        response.towerName = "Error"
    db.update_session(SESSION_ID)
    return response


# GET ROUTE FOR GETTING USER STATISTICS
@app.get('/defender')
def get_user_statistics(nickname: Nickname):
    '''
        NOTE: requests.get("http://localhost:1337/defender", data=json.dumps({"nickname":"some_nickname"}))

        Nickname model:
        nickname: str

        returns UserStatistics model

            NOTE:UserStatistics model:
                attack_points_generated: int
                defense_points_generated: int
    '''

    db = Database()
    statistics = db.get_user_statistics(nickname)
    return statistics


# GET ROUTE FOR GETTING TOWER STATISTICS
@app.get('/tower')
def get_tower_data(tower: Nickname):
    '''
        NOTE: requests.get("http://localhost:1337/tower", data=json.dumps({"nickname":"some_nickname"}))

        returns Item model

            NOTE:Item model:
            #SERVER SENDING MESSAGE INFORMATIONS:
                towerName: str = None
                towerHealth: int = None
                towerDefense: int = None
                towerDefenders: int = None
                serverUri: str = None

            #ENEMY SERVER INFORMATIONS:
                enemyTowerDefenders: int = None
                enemyTowerHealth: int = None
                enemyTowerName: str = None 
    '''

    db = Database()
    statistics = db.get_tower_statistics(tower.nickname, SESSION_ID)
    data = Message()
    data.shield = statistics.towerDefense
    data.health = statistics.towerHealth
    return data


# PUT ROUTE FOR UPDATING DEFENDERS STATISTICS
@app.put("/defender")
def update_defender(message: Message):
    '''
        NOTE: requests.put('http://localhost:1337/defender', data=json.dumps(Message model))

        NOTE:Message model:
            message: str = ''
            tower: str = ''
            sender: str = ''
            health: int = 0
            shield: int = 0

    '''
    logger.log_info("UPDATE DEFENDER CALLED")

    db = Database()
    updated = update_defender_help(db, message)
    db.update_user(message.sender, updated)
    if(message.message == "shield"):
        db.update_tower_defense(SESSION_ID, -100, message.tower)


# PUT ROUTE FOR UPDATING TOWERS STATISTICS
@app.put("/tower")
def update_tower(message: Message):
    '''
        NOTE: requests.put('http://localhost:1337/tower', data=json.dumps(Message model))

        NOTE:Message model:
            message: str = ''
            tower: str = ''
            sender: str = ''
            health: int = 0
            shield: int = 0

    '''

    db = Database()
    if(message.message == "health_attacked" or message == "shield"):
        if(message.message == "health_attacked"):
            logger.log_info(
                f"UPDATE TOWER CALLED WITH HEALTH {message.health} HEALTH_ATACKED")

            db.update_tower_health(SESSION_ID, message.health, message.tower)
        db.update_tower_defense(SESSION_ID, message.shield, message.tower)
    else:
        updated = update_tower_help(db, message, SESSION_ID)

        db.update_tower(SESSION_ID, updated)
        MESSAGE["message"] = message.message
        MESSAGE[updated.towerName] = updated.towerHealth
        MESSAGE[updated.enemyTowerName] = updated.enemyTowerHealth
        MESSAGE[updated.towerName + ' Defenders'] = updated.towerDefenders
        MESSAGE[updated.enemyTowerName +
                ' Defenders'] = updated.enemyTowerDefenders
        sender.send(MESSAGE, ["Hocus", "Pocus"])


if __name__ == "__main__":
    db = Database()
    SESSION_ID = db.create_session()
    amqp = threading.Thread(target=start_amqp)
    amqp.start()
    start_unicorn(app, HOST, PORT)
