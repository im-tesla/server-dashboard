import bcrypt

hashed = bcrypt.hashpw(b"not this time :)", bcrypt.gensalt())
print(hashed.decode())