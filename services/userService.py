from typing import Dict
from models.userModel import UserModel
from models.personModel import PersonModel
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from repositories.userRepository import UserRepository
from repositories.personRepository import PersonRepository
from utils.userUtil import validate_registration_data, validate_login_data
import os

ALLOWED_PHOTO_EXT = {"png", "jpg", "jpeg", "webp"}

def _allowed_photo(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PHOTO_EXT

class UserService:
    #Servicio con lógica de negocio para los usuarios

    @staticmethod
    def create_user(identification: str, first_name: str, last_name: str, phone: str, email: str, password: str) -> Dict:
        # Crea un nuevo usuario con validaciones

        errors = validate_registration_data(identification, first_name, last_name, phone, email, password)

        if errors:
            return {
                "success": False,
                "message": ", ".join(errors)
            }

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
            person = PersonModel(user_id,identification,first_name,last_name,phone)
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

            profile = {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "identification": person.identification if person else "",
                "first_name": person.first_name if person else "",
                "last_name": person.last_name if person else "",
                "phone": person.phone if person else "",
                "profile_photo": person.profile_photo if person else None
            }

            return {
                "success": True,
                "message": "Usuario encontrado",
                "user": profile
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error al buscar el usuario: {e}"
            }
    
    @staticmethod
    def update_profile(user_id: str, first_name: str, last_name: str, phone: str,
                       photo_file=None, upload_folder: str = None) -> Dict:
        """Actualiza los datos personales y/o foto de perfil del usuario."""
        try:
            person = PersonRepository.find_by_user_id(user_id)
            if not person:
                return {"success": False, "message": "Perfil no encontrado"}

            data = {
                "first_name": first_name.strip(),
                "last_name":  last_name.strip(),
                "phone":      phone.strip()
            }

            if photo_file and photo_file.filename:
                if not _allowed_photo(photo_file.filename):
                    return {"success": False, "message": "Formato de foto no permitido (jpg, png, webp)"}
                import uuid
                ext = photo_file.filename.rsplit(".", 1)[1].lower()
                filename = f"{user_id}.{ext}"
                if upload_folder:
                    photo_file.save(os.path.join(upload_folder, filename))
                data["profile_photo"] = f"/img/profiles/{filename}"

            PersonRepository.update_by_user_id(user_id, data)
            return {"success": True, "message": "Perfil actualizado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar perfil: {e}"}

    @staticmethod
    def get_all_users_with_persons() -> Dict:
        """Retorna todos los usuarios con sus datos personales."""
        try:
            users = UserRepository.find_all()
            result = []
            for u in users:
                p = PersonRepository.find_by_user_id(u.id)
                result.append({
                    "id":            u.id,
                    "email":         u.email,
                    "role":          u.role,
                    "is_active":     u.is_active,
                    "first_name":    p.first_name if p else "",
                    "last_name":     p.last_name if p else "",
                    "phone":         p.phone if p else "",
                    "identification": p.identification if p else "",
                    "profile_photo": p.profile_photo if p else None
                })
            return {"success": True, "users": result}
        except Exception as e:
            return {"success": False, "users": [], "message": f"Error: {e}"}

    @staticmethod
    def toggle_user_active(user_id: str) -> Dict:
        try:
            user = UserRepository.find_by_id(user_id)
            if not user:
                return {"success": False, "message": "Usuario no encontrado"}
            new_status = not user.is_active
            UserRepository.update(user_id, {"is_active": new_status})
            msg = "activado" if new_status else "desactivado"
            return {"success": True, "message": f"Usuario {msg}"}
        except Exception as e:
            return {"success": False, "message": f"Error: {e}"}

    @staticmethod
    def login_user(email: str, password: str) -> Dict:
        #Flujo de autenticación

        errors = validate_login_data(email, password)

        if errors:
            return {
                "success": False,
                "message": ", ".join(errors)
            }

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