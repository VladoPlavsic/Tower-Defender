import psycopg2
from models.models import Towermodel, Defender, Session, Item, UserStatistics


class Database:

    '''
    DATABASE NAME, CREDIENTALS, HOST and PORT 
    '''
    # DOCKER SETUP
    '''
    __DB_NAME = 'app'
    __PASSWORD = 'docker'
    __USER = 'docker'
    __HOST = 'localhost'
    __PORT = '32768'
    '''

    __DB_NAME = 'app'
    __PASSWORD = 'newpassword98'
    __USER = 'postgres'
    __HOST = 'localhost'
    __PORT = '5432'
    # LATER MAKE THEM AS CONSTRUCTOR PARAMETERS

    def __init__(self):
        '''
        1)We connect to Database with credientals from above calling connect method
        2)We acquire cursor from connection'
        3)Create tables if the don't exist
        '''

        self.__CONNECTION = self.__connect()
        self.__CUR = self.__CONNECTION.cursor()
        self.__create_tables()

    def __connect(self):
        return psycopg2.connect(host=self.__HOST, dbname=self.__DB_NAME,
                                user=self.__USER, password=self.__PASSWORD,
                                port=self.__PORT)

    def __create_tables(self):
        '''
        Creating tables we need for the session, in case they don't exist
        TABLES:
        1) Session (id, time_created, global_defender_count, hocus_tower, pocus_tower)
        2) Tower (id, helth, defense, session, defender_count) NOTE: (id,session) pair is UNIQUE
        3) Defender (nickname, attack_points_generated, defense_points_generated, tower) NOTE: nickname has to be UNIQUE
        '''

        self.__CUR.execute(
            f"CREATE TABLE IF NOT EXISTS session (id SERIAL PRIMARY KEY, time_created timestamp, global_defender_count INT NOT NULL, hocus_tower CHAR(5), pocus_tower CHAR(5))")
        self.__CUR.execute(
            f"CREATE TABLE IF NOT EXISTS tower (id char(5) NOT NULL, health INT NOT NULL, defense INT NOT NULL, session INT NOT NULL, defender_count INT NOT NULL, unique(id, session))")
        self.__CUR.execute(
            f"CREATE TABLE IF NOT EXISTS defender (nickname TEXT PRIMARY KEY, attack_points_generated INT NOT NULL, defense_points_generated INT NOT NULL, tower CHAR(5))")
        self.__CONNECTION.commit()

    def create_session(self):
        ''' 
        create_session() -> returning session ID
        Creating new session every time we create a Database object
        '''
        self.__CUR.execute(
            f"INSERT INTO session (time_created, global_defender_count, hocus_tower, pocus_tower) VALUES (now() ,0, 'Hocus', 'Pocus') RETURNING id")
        session_id = self.__CUR.fetchone()[0]
        self.__CONNECTION.commit()
        self.__create_towers(session_id)
        return session_id

    def __create_towers(self, session_id):
        '''
        Creating two towers and inserting them in tower table
        Initial health value for both towers is NOTE: 5000 HP
        '''

        self.__CUR.execute(
            f"INSERT INTO tower (id, health, defense, session, defender_count) VALUES ('Hocus', 5000, 0, {session_id}, 0)")
        self.__CUR.execute(
            f"INSERT INTO tower (id, health, defense, session, defender_count) VALUES ('Pocus', 5000, 0, {session_id}, 0)")
        self.__CONNECTION.commit()

    def create_user(self, user: Defender):
        '''
        create_user(user:Defender) -> returns False in case that user with given nickname already exists in DB,
        else inserts new user to Defender table and returns True

        NOTE: Defender model:
            nickname: str
            attack_points_generated: int
            defense_points_generated: int
            tower: str

        '''

        if(self.__user_exists(user.nickname)):
            return False
        self.__CUR.execute(f"INSERT INTO defender VALUES ('{user.nickname}', \
        {user.attack_points_generated}, {user.defense_points_generated}, '{user.tower}')")
        self.__CONNECTION.commit()
        return True

    def __user_exists(self, username):
        '''
        __user_exists(username) -> Checks if user with given username already exists in table Defender
        if yes returns True
        else returns False
        '''

        self.__CUR.execute(
            f"SELECT nickname FROM defender WHERE nickname LIKE '{username}'")
        if(self.__CUR.fetchone() == None):
            return False
        return True

    def update_session(self, session_id):
        '''
        Updating session when a new user is connected
        Basicly increse global_defender_count by one and that's it
        '''

        self.__CUR.execute(
            f"UPDATE session SET global_defender_count = global_defender_count + 1 WHERE id = {session_id}")
        self.__CONNECTION.commit()

    def update_tower(self, session_id, data: Item):
        '''
        update_tower(session_id, data)

        Updating both towers at once with UPDATED HEALTH and DEFENSE for SENDER tower, and updated HEALTH for ENEMY tower 

        NOTE: session_id: ID of currently active session

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

        self.__CUR.execute(f"UPDATE tower SET health={data.towerHealth}, \
                           defender_count={data.towerDefenders}, defense={data.towerDefense} WHERE session={session_id} AND id LIKE '{data.towerName}'")
        enemy_tower_name = "Hocus" if data.towerName == "Pocus" else "Pocus"
        self.__CUR.execute(
            f"UPDATE tower SET health = {data.enemyTowerHealth} WHERE session={session_id} AND id LIKE '{enemy_tower_name}'")
        self.__CONNECTION.commit()

    def update_tower_health(self, session_id, health, tower_name):
        '''
            update_tower_health(session_id, health, tower_name)

                session_id: ID of currently running session
                health: new health status of given tower
                tower_name: Hocus or Pocus -> what tower should be updated
        '''

        self.__CUR.execute(
            f"UPDATE tower SET health={health} WHERE session={session_id} AND id LIKE '{tower_name}'")
        self.__CONNECTION.commit()

    def update_tower_defense(self, session_id, shield, tower_name):
        '''
            update_tower_defense(session_id, shield, tower_name)

                session_id: ID of currently running session
                NOTE: shield: new shield status of given tower or (any negative numer in case we just want to increse shield status by +150 units)
                tower_name: Hocus or Pocus -> what tower should be updated
        '''

        if(shield < 0):
            self.__CUR.execute(
                f"UPDATE tower SET defense=defense + 150 WHERE session={session_id} AND id LIKE '{tower_name}' RETURNING defense")
        else:  # TEST shield = 0 case
            self.__CUR.execute(
                f"UPDATE tower SET defense={shield} WHERE session={session_id} AND id LIKE '{tower_name}'")
        self.__CONNECTION.commit()

    def update_user(self, nickname, points: UserStatistics):
        '''
            update_user(nickname, points)

                nickname: string, nickname of user we want to update

                NOTE:UserStatistics model:
                    attack_points_generated: int
                    defense_points_generated: int
        '''

        self.__CUR.execute(
            f"UPDATE defender SET attack_points_generated= {points.attack_points_generated}, defense_points_generated= {points.defense_points_generated} \
            WHERE nickname LIKE '{nickname}'")
        self.__CONNECTION.commit()

    def delete_user(self, nickname):
        '''
            delete_user(nickname) Deletes user with given nickname from Defender table
        '''

        self.__CUR.execute(
            f"DELETE FROM defender WHERE nickname LIKE '{nickname}'")
        self.__CONNECTION.commit()

    def get_tower_statistics(self, tower, session_id):
        '''
            get_tower_statistics(tower, session_id) -> returning Item object

                tower: Statistics of what tower do we want to retrive 
                session_id: ID of currently active session

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

        self.__CUR.execute(
            f"SELECT health, defense, defender_count FROM tower WHERE id LIKE '{tower}' AND session = {session_id}")
        item = Item()
        data = self.__CUR.fetchone()
        item.towerName = tower
        item.towerHealth = data[0]
        item.towerDefense = data[1]
        item.towerDefenders = data[2]

        enemy_tower = "Hocus" if tower == "Pocus" else "Pocus"

        self.__CUR.execute(
            f"SELECT health, defender_count FROM tower WHERE id LIKE '{enemy_tower}' AND session = {session_id}")
        data = self.__CUR.fetchone()
        item.enemyTowerHealth = data[0]
        item.enemyTowerDefenders = data[1]
        item.enemyTowerName = "Hocus" if tower == "Pocus" else "Pocus"
        item.serverUri = "localhost:666" if tower == "Hocus" else "localhost:999"
        return item

    def get_user_statistics(self, nickname):
        '''
            get_user_statistics(nickname) -> returns UserStatistics object if user exists ELSE returns False

                nickname: user nickname whoes statistics we want to retrive 

            NOTE:UserStatistics model:
                attack_points_generated: int
                defense_points_generated: int
        '''

        if self.__user_exists(nickname):
            self.__CUR.execute(
                f"SELECT attack_points_generated, defense_points_generated FROM defender WHERE nickname LIKE '{nickname}'")
            statistics = UserStatistics()
            data = self.__CUR.fetchone()
            statistics.attack_points_generated = data[0]
            statistics.defense_points_generated = data[1]
            return statistics
        else:
            return False

    def get_defender_count(self, tower, session_id):
        '''
            get_defender_count(tower, session_id) -> returns how many defenders there are in a tower at curently active session 
        '''
        self.__CUR.execute(
            f"SELECT defender_count FROM tower WHERE session = {session_id} AND id LIKE '{tower}'")
        return self.__CUR.fetchone()[0]
