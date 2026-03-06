from database.mongoDb import DatabaseConnection
from models.personModel import PersonModel
from typing import Optional

class PersonRepository:
    # Repositorio para operaciones con la BD de persistencia de datos personales del usuario

    COLLECTION_NAME = "persons"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)
    
    @classmethod
    def create(cls, person: PersonModel) -> str:
        #Crea un nuevo usuario en la bd
        collection = cls._get_collection()
        result = collection.insert_one(person.to_dict())
        return str(result.inserted_id)
    
    @classmethod
    def find_by_user_id(cls, user_id: str) -> Optional[PersonModel]:
        #Buscar datos por user_id de la colección user
        collection = cls._get_collection()
        data = collection.find_one({"user_id": user_id})
        if data:
            return PersonModel.from_dict(data)
        return None
    
    @classmethod
    def find_by_identification(cls, identification: str) -> Optional[PersonModel]:
        #Buscar datos por identificacion
        collection = cls._get_collection()
        data = collection.find_one({"identification": identification})
        if data:
            return PersonModel.from_dict(data)
        return None
    
    @classmethod
    def exist_by_identification(cls, identification: str) -> bool:
        #Existe identificacion
        collection = cls._get_collection()
        return collection.find_one({"identification": identification}) is not None