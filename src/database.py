import psycopg2
from models.models import Towermodel, Defender, Session, Item, UserStatistics


class Database:

    __DB_NAME = 'app'
    __PASSWORD = 'newpassword98'
    __USER = 'postgres'
    __HOST = 'localhost'
    __PORT = '5432'

    def __init__(self):
        self.__CONNECTION = self.__connect()
        self.__CUR = self.__CONNECTION.cursor()
        self.__create_tables()

    def __connect(self):
        return psycopg2.connect(host=self.__HOST, dbname=self.__DB_NAME,
                                user=self.__USER, password=self.__PASSWORD,
                                port=self.__PORT)

    def __create_tables(self):
        self.__CUR.execute(
            f"CREATE TABLE IF NOT EXISTS session (id SERIAL PRIMARY KEY, time_created timestamp, global_defender_count INT NOT NULL, hocus_tower CHAR(5), pocus_tower CHAR(5))")
        self.__CUR.execute(
            f"CREATE TABLE IF NOT EXISTS tower (id char(5) NOT NULL, health INT NOT NULL, defense INT NOT NULL, session INT NOT NULL, defender_count INT NOT NULL, unique(id, session))")
        self.__CUR.execute(
            f"CREATE TABLE IF NOT EXISTS defender (nickname TEXT PRIMARY KEY, attack_points_generated INT NOT NULL, defense_points_generated INT NOT NULL, tower CHAR(5))")
        self.__CONNECTION.commit()

    def create_session(self):
        self.__CUR.execute(
            f"INSERT INTO session (time_created, global_defender_count, hocus_tower, pocus_tower) VALUES (now() ,0, 'Hocus', 'Pocus') RETURNING id")
        session_id = self.__CUR.fetchone()[0]
        self.__CONNECTION.commit()
        self.__create_towers(session_id)
        return session_id

    def __create_towers(self, session_id):
        self.__CUR.execute(
            f"INSERT INTO tower (id, health, defense, session, defender_count) VALUES ('Hocus', 5000, 0, {session_id}, 0)")
        self.__CUR.execute(
            f"INSERT INTO tower (id, health, defense, session, defender_count) VALUES ('Pocus', 5000, 0, {session_id}, 0)")
        self.__CONNECTION.commit()

    def create_user(self, user: Defender):
        if(self.__user_exists(user.nickname)):
            return False
        self.__CUR.execute(f"INSERT INTO defender VALUES ('{user.nickname}', \
        {user.attack_points_generated}, {user.defense_points_generated}, '{user.tower}')")
        self.__CONNECTION.commit()
        return True

    def __user_exists(self, username):
        self.__CUR.execute(
            f"SELECT nickname FROM defender WHERE nickname LIKE '{username}'")
        if(self.__CUR.fetchone() == None):
            return False
        return True

    def update_session(self, session_id):
        self.__CUR.execute(
            f"SELECT global_defender_count FROM session WHERE id = {session_id}")
        count = self.__CUR.fetchone()[0]
        self.__CUR.execute(
            f"UPDATE session SET global_defender_count = {count + 1} WHERE id = {session_id}")
        self.__CONNECTION.commit()

    def update_tower(self, session_id, data: Item):
        self.__CUR.execute(f"UPDATE tower SET health={data.towerHealth}, \
                           defender_count={data.towerDefenders}, defense={data.towerDefense} WHERE session={session_id} AND id LIKE '{data.towerName}'")
        enemyTowerName = "Hocus" if data.towerName == "Pocus" else "Pocus"
        self.__CUR.execute(
            f"UPDATE tower SET health = {data.enemyTowerHealth} WHERE session={session_id} AND id LIKE '{enemyTowerName}'")
        self.__CONNECTION.commit()

    def update_user(self, nickname, points: UserStatistics):
        self.__CUR.execute(
            f"UPDATE defender SET attack_points_generated= {points.attack_points_generated}, defense_points_generated= {points.defense_points_generated} \
            WHERE nickname LIKE '{nickname}'")
        self.__CONNECTION.commit()

    def delete_user(self, nickname):
        self.__CUR.execute(
            f"DELETE FROM defender WHERE nickname LIKE '{nickname}'")
        self.__CONNECTION.commit()

    def get_tower_statistics(self, tower, session_id):
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
        '''Not GOOOOOOOD'''  # HEARUAKLHERAJIROOJHSADJHABKJSDLHAKSBDIAJLSDBHALDJSKJLDASLJDASLNDLJASBD
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

    # Not checked

    def get_defender_count(self, tower, session_id):
        self.__CUR.execute(
            f"SELECT defender_count FROM tower WHERE session = {session_id} AND id LIKE '{tower}'")
        return self.__CUR.fetchone()[0]


if __name__ == "__main__":
    db = Database()
    session_id = db.create_session()
    db.update_session(session_id)
