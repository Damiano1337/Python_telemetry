import json
from encryption_utils import encrypt_file

# Krok 1: Wczytaj dane z istniejącego users.json
with open("users.json", "r") as f:
    users_data = json.load(f)

# Krok 2: Zaszyfruj dane i zapisz jako users.json.encrypted
encrypt_file(users_data, "haslo123")  # <- tu wpisz swoje hasło admina
