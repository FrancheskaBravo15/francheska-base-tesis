
from database.mongoDb import DatabaseConnection
from models.userModel import UserModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

class UserRepository:
    # Repositorio para operaciones con la BD de persistencia de usuarios

    COLLECTION_NAME = "users"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)
    
    @classmethod
    def create(cls, user: UserModel) -> str:
        #Crea un nuevo usuario en la bd
        try:
            collection = cls._get_collection()
            result = collection.insert_one(user.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear un nuevo usuario en la BD: {e}")
            raise
    
    @classmethod
    def find_all(cls) -> List[UserModel]:
        #Obtener todos los registros
        try:
            collection = cls._get_collection()
            result = collection.find()
            return [UserModel.from_dict(user) for user in list(result)]
        except PyMongoError as e:
            print(f"Error al obtener todos los registros de la BD: {e}")
            raise
    
    @classmethod
    def find_by_id(cls, user_id: str) -> Optional[UserModel]:
        #Buscar usuario por id
        try:
            collection = cls._get_collection()
            data = collection.find_one({"_id": ObjectId(user_id)})
            if data:
                return UserModel.from_dict(data)
            return None
        except PyMongoError as e:
            print(f"Error al buscar el usuario por Id en la BD: {e}")
            raise
    
    @classmethod
    def find_by_email(cls, email: str) -> Optional[UserModel]:
        #Buscar usuario por email
        try:
            collection = cls._get_collection()
            data = collection.find_one({"email": email})
            if data:
                return UserModel.from_dict(data)
            return None
        except PyMongoError as e:
            print(f"Error al buscar el usuario por Email en la BD: {e}")
            raise
    
    @classmethod
    def exist_by_email(cls, email: str) -> bool:
        #Existe email
        try:
            collection = cls._get_collection()
            return collection.find_one({"email": email}) is not None
        except PyMongoError as e:
            print(f"Error al buscar un Email en la BD: {e}")
            raise
    
    @classmethod
    def delete_by_id(cls, user_id: str) -> None:
        #Eliminar por id de usuario
        try:
            collection = cls._get_collection()
            collection.delete_one({"_id":ObjectId(user_id)})
        except PyMongoError as e:
            print(f"Error al eliminar el usuario por Id en la BD: {e}")
            raise

    @classmethod
    def find_by_role(cls, role: str) -> List[UserModel]:
        #Obtiene los usuarios con un rol específico
        try:
            collection = cls._get_collection()
            return [UserModel.from_dict(u) for u in collection.find({"role": role})]
        except PyMongoError as e:
            print(f"Error al buscar usuario por rol en la BD: {e}")
            raise

    @classmethod
    def update(cls, user_id: str, data: dict) -> None:
        #Actualiza campos del usuario
        try:
            collection = cls._get_collection()
            collection.update_one({"_id": ObjectId(user_id)}, {"$set": data})
        except PyMongoError as e:
            print(f"Error al actualizar usuario en la BD: {e}")
            raise