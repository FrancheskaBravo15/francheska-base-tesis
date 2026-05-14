from typing import Dict
from models.userModel import UserModel
from models.personModel import PersonModel
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from repositories.userRepository import UserRepository
from repositories.personRepository import PersonRepository
from utils.userUtil import validate_registration_data, validate_login_data
from services.emailService import EmailService
import os
import secrets
from datetime import datetime, timedelta

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

            EmailService.send_welcome(email, first_name.strip())
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
    def request_password_reset(email: str, reset_url: str) -> Dict:
        """Genera token de recuperación y envía el correo."""
        try:
            user = UserRepository.find_by_email(email.strip().lower())
            if not user:
                # No revelar si el email existe o no
                return {"success": True, "message": "Si ese correo está registrado, recibirás un enlace en breve."}

            person = PersonRepository.find_by_user_id(user.id)
            first_name = person.first_name if person else "usuaria"

            token  = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(hours=1)
            UserRepository.save_reset_token(user.id, token, expiry)

            full_url = reset_url.replace("__TOKEN__", token)
            EmailService.send_password_reset(user.email, first_name, full_url)

            return {"success": True, "message": "Si ese correo está registrado, recibirás un enlace en breve."}
        except Exception as e:
            return {"success": False, "message": f"Error al procesar la solicitud: {e}"}

    @staticmethod
    def reset_password(token: str, new_password: str, confirm_password: str) -> Dict:
        """Valida el token y actualiza la contraseña."""
        if not token:
            return {"success": False, "message": "Token inválido."}
        if len(new_password) < 8:
            return {"success": False, "message": "La contraseña debe tener al menos 8 caracteres."}
        if new_password != confirm_password:
            return {"success": False, "message": "Las contraseñas no coinciden."}
        try:
            user = UserRepository.find_by_reset_token(token)
            if not user:
                return {"success": False, "message": "El enlace es inválido o ya expiró."}
            UserRepository.update(user.id, {"password": generate_password_hash(new_password)})
            UserRepository.clear_reset_token(user.id)
            return {"success": True, "message": "Contraseña actualizada exitosamente. Ahora puedes iniciar sesión."}
        except Exception as e:
            return {"success": False, "message": f"Error al restablecer la contraseña: {e}"}

    @staticmethod
    def change_password(user_id: str, current_password: str, new_password: str, confirm_password: str) -> Dict:
        """Cambia la contraseña desde el perfil (requiere la contraseña actual)."""
        if len(new_password) < 8:
            return {"success": False, "message": "La nueva contraseña debe tener al menos 8 caracteres."}
        if new_password != confirm_password:
            return {"success": False, "message": "Las contraseñas no coinciden."}
        try:
            user = UserRepository.find_by_id(user_id)
            if not user:
                return {"success": False, "message": "Usuario no encontrado."}
            if not check_password_hash(user.password, current_password):
                return {"success": False, "message": "La contraseña actual es incorrecta."}
            UserRepository.update(user_id, {"password": generate_password_hash(new_password)})
            return {"success": True, "message": "Contraseña cambiada exitosamente."}
        except Exception as e:
            return {"success": False, "message": f"Error al cambiar la contraseña: {e}"}

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