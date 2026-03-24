from datetime import datetime

class PersonModel:
    #Modelo de dominio para los datos personales del usuario
    def __init__(self, user_id, identification, first_name, last_name, phone, id=None, profile_photo=None):
        self.id = id
        self.user_id = user_id
        self.identification = identification
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.profile_photo = profile_photo
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'PersonModel':
        #Crear un modelo de diccionario de MongoDB
        person = cls(
            user_id = data["user_id"],
            identification = data["identification"],
            first_name = data["first_name"],
            last_name = data["last_name"],
            phone = data["phone"],
            profile_photo = data.get("profile_photo", None)
        )
        if "_id" in data:
            person.id = str(data["_id"])
        return person

    def to_dict(self) -> dict:
        #Convertir el modelo a un diccionario para MongoDB
        return {
            "user_id": self.user_id,
            "identification": self.identification,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "phone": self.phone,
            "profile_photo": self.profile_photo,
            "created_at": self.created_at
        }

    def __repr__(self):
        return f"PersonModel(user_id={self.user_id}, first_name={self.first_name}, last_name={self.last_name})"