import sqlite3
from contextlib import closing


class Operator:
    def __init__(self, uuid: int, callsign: str, admin: bool):
        self.uuid = uuid
        self.callsign = callsign
        self.admin = admin


class BotDatabase:
    def __init__(self, filename):
        self.connection = sqlite3.connect(filename)

        with closing(self.connection.cursor()) as cursor:
            cursor.execute(
                '''CREATE TABLE IF NOT EXISTS operators 
                (uuid INTEGER, callsign TEXT, admin INTEGER)'''
            )

    def close(self):
        self.commit()
        self.connection.close()

    def commit(self):
        self.connection.commit()

    def get_total_changes(self):
        return self.connection.total_changes

    def get_operator(self, operator_id: int):
        try:
            with closing(self.connection.cursor()) as cursor:
                row = cursor.execute('SELECT * FROM operators WHERE uuid = ?', (operator_id,)).fetchall()[0]
        except IndexError:
            return None

        return Operator(row[0], row[1], row[2])

    def get_operators(self):
        with closing(self.connection.cursor()) as cursor:
            rows = cursor.execute('SELECT * FROM operators').fetchall()

        operators = []

        for row in rows:
            uuid = row[0]
            callsign = row[1]
            admin = row[2]
            operators.append(Operator(uuid, callsign, admin))

        return operators

    def add_operator(self, uuid: int, callsign: str, admin: bool = False):
        admin_int = 1 if admin else 0

        with closing(self.connection.cursor()) as cursor:
            cursor.execute('INSERT INTO operators VALUES (?, ?, ?)',
                           (uuid, callsign, admin_int))

    def delete_operator(self, operator_id: int):
        with closing(self.connection.cursor()) as cursor:
            cursor.execute('DELETE FROM operators WHERE uuid = ?', (operator_id,))

    def update_operator_callsign(self, uuid: int, new_call: str):
        with closing(self.connection.cursor()) as cursor:
            cursor.execute('UPDATE operators SET callsign = ? WHERE uuid = ?', (new_call, uuid))

    def update_operator_uuid(self, callsign: str, new_uuid: int):
        with closing(self.connection.cursor()) as cursor:
            cursor.execute('UPDATE operators SET uuid = ? WHERE callsign = ?', (new_uuid, callsign))
