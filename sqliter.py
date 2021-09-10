import sqlite3


class SQLighter:

    def __init__(self, db_file):
        self.connection = sqlite3.connect(db_file)
        self.cursor = self.connection.cursor()

    def get_watchlist(self, chat_id):
        with self.connection:
            return self.cursor.execute("SELECT name, max_price, started FROM 'collections' WHERE chat_id = ?",
                                       (chat_id,)).fetchall()

    def get_collections(self):
        with self.connection:
            return self.cursor.execute(
                "SELECT name, chat_id, max_price, last_nft_id FROM 'collections' WHERE started = 1").fetchall()

    def collection_exists(self, name, chat_id):
        with self.connection:
            result = self.cursor.execute("SELECT * FROM 'collections' WHERE name = ? and chat_id = ?",
                                         (name, chat_id)).fetchall()
            return bool(len(result))

    def add_collection(self, name, chat_id):
        with self.connection:
            return self.cursor.execute("INSERT INTO 'collections' ('name', 'chat_id') VALUES (?, ?)", (name, chat_id))

    def delete_collection(self, name, chat_id):
        with self.connection:
            return self.cursor.execute("DELETE FROM 'collections' WHERE name = ? and chat_id = ?", (name, chat_id))

    def start_watch(self, name, max_price, chat_id):
        with self.connection:
            return self.cursor.execute(
                "UPDATE 'collections' SET max_price = ?, started = 1 WHERE name = ? and chat_id = ?",
                (max_price, name, chat_id))

    def stop_watch(self, name, chat_id):
        with self.connection:
            return self.cursor.execute(
                "UPDATE 'collections' SET started = 0 WHERE name = ? and chat_id = ?",
                (name, chat_id))

    def stop_all(self, chat_id):
        with self.connection:
            return self.cursor.execute(
                "UPDATE 'collections' SET started = 0 WHERE chat_id = ?",
                (chat_id,))

    def update_last_nft_id(self, name, chat_id, nft_id):
        with self.connection:
            return self.cursor.execute(
                "UPDATE 'collections' SET last_nft_id = ? WHERE name = ? and chat_id = ?",
                (nft_id, name, chat_id))

    def close(self):
        self.connection.close()
