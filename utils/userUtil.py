import re
 
def validate_required(value: str, field_name: str, min_length: int = 1) -> str | None:
    #Valida que un campo no esté vacío y tenga una longitud mínima
    if not value or len(value) < min_length:
        return f"{field_name} debe tener al menos {min_length} caracteres"
    return None
 
def validate_email(email: str) -> str | None:
    #Valida que el email tenga un formato correcto
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email or not re.match(email_regex, email):
        return "El email no tiene un formato válido"
    return None
 
def validate_password(password: str) -> str | None:
    #Valida que la contraseña tenga al menos 8 caracteres
    if not password or len(password) < 8:
        return "La contraseña debe tener al menos 8 caracteres"
    return None
 
def validate_cedula(cedula: str) -> str | None:
    #Valida que la cédula ecuatoriana sea válida
    if not cedula or not cedula.isdigit():
        return "La cédula debe contener solo números"
 
    if len(cedula) != 10:
        return "La cédula debe tener exactamente 10 dígitos"
 
    #Los dos primeros dígitos corresponden a la provincia (01-24)
    provincia = int(cedula[:2])
    if provincia < 1 or provincia > 24:
        return "La cédula tiene un código de provincia inválido"
 
    #El tercer dígito debe ser entre 0 y 5 (persona natural)
    if int(cedula[2]) > 5:
        return "La cédula tiene un tercer dígito inválido"
 
    #Algoritmo de validación del dígito verificador (módulo 10)
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    suma = 0
 
    for i in range(9):
        resultado = int(cedula[i]) * coeficientes[i]
        if resultado > 9:
            resultado -= 9
        suma += resultado
 
    digito_verificador = 10 - (suma % 10)
    if digito_verificador == 10:
        digito_verificador = 0
 
    if digito_verificador != int(cedula[9]):
        return "La cédula no es válida"
 
    return None
 
def validate_registration_data(identification: str, first_name: str, last_name: str,phone: str, email: str, password: str) -> list[str]:
    #Valida todos los campos del formulario de registro y retorna lista de errores
    errors = []
 
    error = validate_cedula(identification)
    if error:
        errors.append(error)
 
    error = validate_required(first_name, "El nombre", 2)
    if error:
        errors.append(error)
 
    error = validate_required(last_name, "El apellido", 2)
    if error:
        errors.append(error)
    error = validate_phone_number(phone)
    if error:
        errors.append(error)
 
    error = validate_email(email)
    if error:
        errors.append(error)
 
    error = validate_password(password)
    if error:
        errors.append(error)
    return errors
 
def validate_phone_number(phone: str) -> str | None:
    if not phone:
        return "El número de teléfono es obligatorio"

    # Convertir a string y eliminar cualquier carácter que no sea número
    phone_str = re.sub(r'\D', '', str(phone))  # elimina todo lo que no sea dígito

    if not phone_str.isdigit():
        return "El número de teléfono debe contener solo números"
    
    if len(phone_str) != 10:
        return "El número de teléfono debe tener exactamente 10 dígitos"
    
    return None

def validate_login_data(email: str, password: str) -> list[str]:
    #Valida los campos de login
    errors = []
 
    error = validate_email(email)
    if error:
        errors.append(error)
 
    error = validate_required(password, "La contraseña", 1)
    if error:
        errors.append(error)
 
    return errors
