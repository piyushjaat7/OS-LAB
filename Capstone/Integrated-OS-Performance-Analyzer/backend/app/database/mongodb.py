from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.core.config import get_settings


class MongoDBManager:
    def __init__(self) -> None:
        self.client: MongoClient | None = None
        self.database: Database | None = None

    def connect(self) -> None:
        if self.client is not None:
            return

        settings = get_settings()

        client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,
        )

        try:
            client.admin.command("ping")
            self.database = client[settings.mongodb_database]
            self.client = client
        except PyMongoError:
            client.close()
            raise

    def disconnect(self) -> None:
        if self.client is not None:
            self.client.close()

        self.client = None
        self.database = None

    def ping(self) -> bool:
        if self.client is None:
            return False

        try:
            return self.client.admin.command("ping").get("ok") == 1
        except PyMongoError:
            return False


mongodb = MongoDBManager()
