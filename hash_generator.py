# hash_generator.py
import bcrypt

passwords = ["admin", "playerpass", "coachpass"]

for pwd in passwords:
    hashed = bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt())
    print(f"{pwd} -> {hashed.decode('utf-8')}")