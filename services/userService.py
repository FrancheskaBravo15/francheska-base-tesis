from typing import Dict
from models.userModel import UserModel
from models.personModel import PersonModel
from werkzeug.security import generate_password_hash, check_password_hash
from repositories.userRepository import UserRepository
from repositories.personRepository import PersonRepository

class UserService:
    #Servicio con lógica de negocio para los usuarios

    @staticmethod
    def create_user(identification: str, first_name: str, last_name: str, email: str, password: str) -> Dict:
        # Crea un nuevo usuario con validaciones

        user_id = None
        
        try:
            if UserRepository.exist_by_email(email):
                return {
                    "success": False,
                    "message": "Ya existe un usuario con ese correo electrónico"
                }
            
            if PersonRepository.exist_by_identification(identification):
                return {
                    "success": False,
                    "message": "Ya existe un usuario con esa identificacion"
                }
            
            #Creación del user
            hashed_password = generate_password_hash(password)
            user = UserModel(email, password=hashed_password, role="client")
            user_id = UserRepository.create(user)
            #Creación del person
            person = PersonModel(user_id,identification,first_name,last_name)
            PersonRepository.create(person)

            return {
                "success": True,
                "message": "Usuario creado exitosamente"
            }
        except Exception as e:
            if user_id:
                UserRepository.delete_by_id(user_id)
            return {
                "success": False,
                "message": f"Error al crear el usuario: {e}"
            }
        
    @staticmethod
    def get_all_users() -> Dict:
        #Obtiene todos los usuarios

        users = UserRepository.find_all()
        
        return{
            "users": users
        }
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Dict:
        #Obtener usuario por id
        try:

            user = UserRepository.find_by_id(user_id)
            if not user:
                return{
                    "success": False,
                    "message": "Usuario no encontrado"
                }
            person = PersonRepository.find_by_user_id(user_id)

            return {
                "success": True,
                "message": "Usuario encontrado",
                "user": person
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al buscar el usuario: {e}"
            }
    
    @staticmethod
    def login_user(email: str, password: str) -> Dict:
        #Flujo de autenticación

        try:
            
            user = UserRepository.find_by_email(email)

            if not user:
                return {
                    "success": False,
                    "message": "Email no existente"
                }
            if not check_password_hash(user.password, password):
                return {
                    "success": False,
                    "message": "Contraseña incorrecta"
                }
            return{
                "success": True,
                "message": "Inicio de sesión exitoso",
                "user_id": user.id
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al iniciar sesión: {e}"
            }