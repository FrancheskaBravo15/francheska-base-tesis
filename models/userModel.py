from datetime import datetime

class UserModel:
    #Modelo de dominio para los usuarios
    def __init__(self, email, password, role, id=None):
        self.id = id
        self.email = email
        self.password = password
        self.role = role
        self.created_at = datetime.now()
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserModel':
        #Crear un modelo de diccionario de MongoDB
        user = cls(
            email = data["email"],
            password = data["password"],
            role = data["role"]
        )
        if "_id" in data:
            user.id = str(data["_id"])
        return user
    
    def to_dict(self) -> dict:
        #Convertir el modelo a un diccionario para MongoDB
        return {
            "email": self.email,
            "password": self.password,
            "role": self.role,
            "created_at": self.created_at
        }
    
    def __repr__(self):
        return f"UserModel(email={self.email}, password={self.password}, role={self.role}, created_at={self.created_at})"