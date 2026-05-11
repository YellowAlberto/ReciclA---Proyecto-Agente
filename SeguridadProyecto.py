from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generar_hash(password: str):
    return pwd_context.hash(password)

def verificar_password(password_plano, password_hasheado):
    return pwd_context.verify(password_plano, password_hasheado)