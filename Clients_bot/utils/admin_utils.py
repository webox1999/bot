import json
import os

ADMINS_FILE = 'data/admins.json'

# Проверяем, существует ли файл, если нет — создаем
if not os.path.exists(ADMINS_FILE):
    with open(ADMINS_FILE, 'w') as f:
        json.dump({"admins": []}, f)

def load_admins():
    with open(ADMINS_FILE, 'r') as f:
        return json.load(f)['admins']

def save_admins(admins):
    with open(ADMINS_FILE, 'w') as f:
        json.dump({"admins": admins}, f, indent=4)

def is_admin(user_id):
    return user_id in load_admins()
