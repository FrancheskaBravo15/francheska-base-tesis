import click
import os
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from models.userModel import UserModel
from models.personModel import PersonModel
from repositories.userRepository import UserRepository
from repositories.personRepository import PersonRepository
 
@click.command('seed-admin')
@with_appcontext
def seed_admin_command():
    #Crea el usuario administrador desde las variables de entorno
    admins = UserRepository.find_by_role("admin")
    if admins:
        click.echo("Ya existe un administrador registrado. Operación cancelada.")
        return
 
    email    = os.getenv("ADMIN_EMAIL")
    password = os.getenv("ADMIN_PASSWORD")
    first_name = os.getenv("ADMIN_FIRST_NAME", "Administrador")
    last_name  = os.getenv("ADMIN_LAST_NAME", "Sistema")
    identification = os.getenv("ADMIN_IDENTIFICATION", "0000000000")
    phone = os.getenv("ADMIN_PHONE", "0000000000")
 
    if not email or not password:
        click.echo("Error: ADMIN_EMAIL y ADMIN_PASSWORD deben estar definidos en el .env")
        return
 
    try:
        hashed_password = generate_password_hash(password)
        user = UserModel(email=email, password=hashed_password, role="admin")
        user_id = UserRepository.create(user)
 
        person = PersonModel(
            user_id        = user_id,
            identification = identification,
            first_name     = first_name,
            last_name      = last_name,
            phone          = phone
        )
        PersonRepository.create(person)
 
        click.echo(f"Administrador creado exitosamente: {email}")
    except Exception as e:
        click.echo(f"Error al crear el administrador: {e}")