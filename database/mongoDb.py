from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import Optional
import atexit
import os

class DatabaseConnection:
    #Patrón de diseño Singleton
    _client: Optional[MongoClient] = None
    _database: Optional[Database] = None

    @classmethod
    def initialize(cls) -> None:
        #Creación de la conexión con MongoDb
        if cls._client is None:
            try:
                #URL de MongoDb
                mongo_uri = os.getenv("MONGO_URI")
                cls._client = MongoClient(mongo_uri)
                #Nombre de la BD en MongoDb
                db_name = os.getenv("DB_NAME")
                cls._database = cls._client[db_name]
                #Verificación de la conexión a mongoDB
                cls._client.server_info()
                print(f"Conectado a MongoDb Correctamente: {db_name}")
                atexit.register(cls.close)
            except ConnectionFailure as e:
                cls._client = None
                cls._database = None
                print(f"Error de conexión a MongoDB: {e}")
                raise
            except ServerSelectionTimeoutError as e:
                cls._client = None
                cls._database = None
                print(f"MongoDB no disponible (timeout): {e}")
                raise

    @classmethod
    def close(cls) -> None:
        #Cierre de conexión de MongoDb
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._database = None
            print(f"Desconectado de MongoDb")
    
    @classmethod
    def get_database(cls) -> Database:
        #Retornar la instancia a la BD
        if cls._database is None:
            raise Exception("Base de datos no inicializada")
        return cls._database
    
    @classmethod
    def get_collection(cls, collection_name: str):
        #Retorna la colección específica (user, products, etc)
        return cls.get_database()[collection_name]
