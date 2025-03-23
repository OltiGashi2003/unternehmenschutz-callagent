import sqlite3
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager

@dataclass
class Client:
    name: str
    vorname: str
    stadt: str
    strasse: int
    anzahl_paket: int
    total: float

class DatabaseDriver:
    def __init__(self, db_path: str = "auto_db.sqlite"):
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create bestellungen table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bestellungen (
                    name TEXT PRIMARY KEY,
                    vorname TEXT NOT NULL,
                    stadt TEXT NOT NULL,
                    strasse TEXT NOT NULL,
                    anzahl_paket INTEGER NOT NULL,
                    total FLOAT NOT NULL
                    
                )
            """)
            conn.commit()

    def create_order(self, name: str, vorname: str, stadt: str, strasse: int, anzahl_paket: int, total: float) -> Client:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO bestellungen (name, vorname, stadt, strasse, anzahl_paket, total) VALUES (?, ?, ?, ?)",
                (name, vorname, stadt, strasse, anzahl_paket, total)
            )
            conn.commit()
            return Client(name=name, vorname=vorname, stadt=stadt, strasse=strasse, anzahl_paket=anzahl_paket, total=total)

    def get_client_by_name(self, name: str) -> Optional[Client]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM bestellungen WHERE name = ?", (name,))
            row = cursor.fetchone()
            if not row:
                return None
            
            return Client(
                name=row[0],
                vorname=row[1],
                stadt=row[2],
                strasse=row[3],
                anzahl_paket=row[4],
                total=row[5]
            )