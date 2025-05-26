import json
import os
from cryptography.fernet import Fernet
from key_utils import generate_key_from_password

# Stały salt do generowania klucza (możesz też trzymać osobno)
SALT = b'\x00\xa1\xb2\xc3\xd4\xe5\xf6g'  # <- zmień to na losowe w praktyce

def encrypt_file(data: dict, password: str, filename="users.json.encrypted"):
    key = generate_key_from_password(password, SALT)
    fernet = Fernet(key)
    encrypted = fernet.encrypt(json.dumps(data).encode())

    with open(filename, "wb") as f:
        f.write(encrypted)

def decrypt_file(password: str, filename="users.json.encrypted") -> dict:
    key = generate_key_from_password(password, SALT)
    fernet = Fernet(key)

    with open(filename, "rb") as f:
        encrypted_data = f.read()

    decrypted = fernet.decrypt(encrypted_data)
    return json.loads(decrypted.decode())
