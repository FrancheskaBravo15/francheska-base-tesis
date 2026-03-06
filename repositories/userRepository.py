
from database.mongoDb import DatabaseConnection
from models.userModel import UserModel
from typing import List, Optional
from bson import ObjectId

class UserRepository:
    # Repositorio para operaciones con la BD de persistencia de usuarios

    COLLECTION_NAME = "users"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)
    
    @classmethod
    def create(cls, user: UserModel) -> str:
        #Crea un nuevo usuario en la bd
        collection = cls._get_collection()
        result = collection.insert_one(user.to_dict())
        return str(result.inserted_id)
    
    @classmethod
    def find_all(cls) -> List[UserModel]:
        #Obtener todos los registros
        collection = cls._get_collection()
        result = collection.find()
        return [UserModel.from_dict(user) for user in list(result)]
    
    @classmethod
    def find_by_id(cls, user_id: str) -> Optional[UserModel]:
        #Buscar datos por id
        collection = cls._get_collection()
        data = collection.find_one({"_id": user_id})
        if data:
            return UserModel.from_dict(data)
        return None
    
    @classmethod
    def find_by_email(cls, email: str) -> Optional[UserModel]:
        #Buscar datos por email
        collection = cls._get_collection()
        data = collection.find_one({"email": email})
        if data:
            return UserModel.from_dict(data)
        return None
    
    @classmethod
    def exist_by_email(cls, email: str) -> bool:
        #Existe email
        collection = cls._get_collection()
        return collection.find_one({"email": email}) is not None
    
    @classmethod
    def delete_by_id(cls, user_id: str) -> None:
        #Eliminar por id de usuario
        collection = cls._get_collection()
        collection.delete_one({"_id":ObjectId(user_id)})
