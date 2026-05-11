from fastapi import Depends, FastAPI, HTTPException, status, Request, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta, timezone
import uvicorn
import modelsProyecto
from databaseProyecto import SessionLocal, engine
from sqlalchemy.orm import Session
import SeguridadProyecto
from SeguridadProyecto import generar_hash 
from typing import Annotated
import os
import shutil
import io
import numpy as np
import onnxruntime as ort
from PIL import Image
from ultralytics import YOLO
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from groq import Groq
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()


model = YOLO("best.onnx", task="detect")

client_groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


modelsProyecto.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Token(BaseModel):
    access_token: str
    token_type: str

registros_mensajes= {}

@app.post("/login",summary="Login de usuario", description="Comprueba las credenciales y genera un token JWT de acceso", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):


    verificar_frecuencia(form_data.username, segundos=10)

    usuario_db = db.query(modelsProyecto.Usuario).filter(modelsProyecto.Usuario.username == form_data.username).first()

    if not usuario_db or not SeguridadProyecto.verificar_password(form_data.password, usuario_db.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ID de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    to_encode = {
        "sub": usuario_db.username,
        "exp": expire,
        "rol": usuario_db.es_admin
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": encoded_jwt, "token_type": "bearer"}

async def verificar_admin(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        es_admin: bool = payload.get("rol") 
        
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    if es_admin is not True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permisos de administrador"
        )
    return {"username": username, "rol": es_admin}



@app.get("/revisarUsuarios", 
    summary="Listar usuarios (Solo Admin)",
    description="Retorna una lista de todos los usuarios registrados. Requiere privilegios de administrador.")
async def revisar_Usuarios(admin_info: dict = Depends(verificar_admin), db: Session = Depends(get_db)):
    usuarios = db.query(modelsProyecto.Usuario).all()
    return usuarios

def verificar_frecuencia(usuario_actual: str, segundos: int = 5):
    ahora = datetime.now()
    if usuario_actual in registros_mensajes:
        ultima_solicitud = registros_mensajes[usuario_actual]
        tiempo_transcurrido = ahora - ultima_solicitud

        if tiempo_transcurrido < timedelta(seconds=segundos):
            segundos_restantes = segundos - int(tiempo_transcurrido.total_seconds())
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Por favor, espera {segundos_restantes} segundos antes de volver a intentarlo"
            )
    registros_mensajes[usuario_actual] = ahora

def agente_inteligente_llm(deteccion: str, confianza: float):

    saludo = "¡Bienvenido! Soy ReciclIA. Estoy aquí para ayudarte a transformar tus hábitos y cuidar el planeta de forma experta. Vamos a hacer que cada residuo cuente."
    
    prompt = f"""
    Eres un ReciclIA, un Agente experto en sostenibilidad y reciclaje. 
    Se ha detectado un objeto mediante visión artificial:
    - Objeto: {deteccion}
    - Confianza: {confianza:.2f}

    INSTRUCCIÓN DE SALUDO:
    Comienza SIEMPRE tu respuesta con esta frase exacta: "{saludo}"


    BASE DE CONOCIMIENTO (ESTRICTA):
    1. CONTENEDOR MARRÓN (Orgánico): Restos de comida, cáscaras de fruta, posos de café, tapones de corcho, servilletas sucias y cualquier residuo de origen BIOLÓGICO.
    2. CONTENEDOR VERDE (Vidrio): Botellas de vidrio, frascos de conservas, tarros de perfume. (¡NUNCA para orgánicos!).
    3. CONTENEDOR AMARILLO (Envases): Plásticos, latas, briks y envases metálicos.
    4. CONTENEDOR AZUL (Papel/Cartón): Cajas de cartón, periódicos, folletos.
    5. CONTENEDOR GRIS (Resto): Pañales, colillas, objetos rotos que no se reciclan.
    6. PUNTO LIMPIO: Pilas, electrónica, muebles, ropa, aceite usado.

    
    Explica al usuario de forma breve y amable:
    1. En qué contenedor debe tirarlo, añade el color especifico del contenedor utilizando la base de conocimientos.
    2. Un dato curioso sobre el reciclaje de ese material.
    
    REGLA CRÍTICA PARA EL PUNTO 3:
    - SI la confianza es menor a 0.5: Añade una advertencia breve diciendo que podrías estar equivocado debido a la baja precisión.
    - SI la confianza es 0.5 o mayor: NO menciones nada sobre la confianza, ni sobre umbrales, ni des explicaciones de por qué estás seguro. Omite este punto totalmente.

    Termina la explicación siempre con esta frase:
    -Recuerda, cada pequeño gesto cuenta, y reciclar correctamente es un paso importante hacia un futuro más sostenible. ¡Gracias por tu contribución!
    """

    chat_completion = client_groq.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile", # Un modelo rápido y capaz
    )
    return chat_completion.choices[0].message.content



#CRUD Usuarios

@app.post("/registrar", 
    summary="Registrar nuevo usuario",
    description="Crea la cuenta de un usuario y lo guarda en la base de datos.",
    status_code=status.HTTP_201_CREATED)
async def registrar_usuario(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    existe = db.query(modelsProyecto.Usuario).filter(modelsProyecto.Usuario.username == form_data.username).first()
    if existe:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    password_con_hash = generar_hash(form_data.password)

    nuevo_usuario = modelsProyecto.Usuario(
        username=form_data.username,
        password_hash=password_con_hash,
        es_admin=False
    )
    db.add(nuevo_usuario)
    db.commit()
    return {"mensaje": "Usuario creado con éxito usando HASH"}


@app.put("/usuarios/actualizarUsuario", 
    summary="Actualizar nombre de usuario",
    description="Actualiza el nombre de usuario del perfil activo.",
    responses={400: {"description": "Nombre en uso"}, 404: {"description": "No encontrado"}})
async def actualizar_username(
    nuevo_username: str,
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username_actual = payload.get("sub")
    
    usuario = db.query(modelsProyecto.Usuario).filter(modelsProyecto.Usuario.username == username_actual).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # 3. Verificar si el nuevo nombre ya está pillado por OTRO usuario
    existe = db.query(modelsProyecto.Usuario).filter(modelsProyecto.Usuario.username == nuevo_username).first()
    if existe and existe.username != username_actual:
        raise HTTPException(status_code=400, detail="Ese nombre de usuario ya está en uso")

    usuario.username = nuevo_username
    db.commit()
    db.refresh(usuario)
    
    return {"message": "Nombre actualizado", "nuevo_username": nuevo_username}

@app.delete("/usuarios/{user}", 
    summary="Eliminar cuenta",
    description="Borra un usuario. Los administradores pueden borrar cualquier cuenta; usuarios normales solo la suya.",
    status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(
    user: str, 
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db),
):

    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username_token = payload.get("sub")
    es_admin: bool = payload.get("rol") 

    usuario = db.query(modelsProyecto.Usuario).filter(modelsProyecto.Usuario.username == user).first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if usuario.username != username_token and not es_admin:
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar esta cuenta")

    db.delete(usuario)
    db.commit()
    
    return None 

@app.post("/detectar-visual", 
    summary="Detección de objetos y Reciclaje",
    description="Analiza una imagen, devuelve la predicción + respuesta del agente y guarda en historial.",
    responses={
        200: {"content": {"image/jpeg": {}}, "description": "Imagen procesada con cajas de detección."},
        429: {"description": "Límite de velocidad excedido"}
    })
async def detectar_visual(file: UploadFile = File(...), token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        usuario = db.query(modelsProyecto.Usuario).filter(modelsProyecto.Usuario.username == username).first()
        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    

    verificar_frecuencia(username, segundos=30)

    contents = await file.read()
    image = Image.open(io.BytesIO(contents)).convert("RGB")
    
    results = model.predict(image, imgsz=640, conf=0.25)[0]

    prediccion_nombre = "Sin detecciones"
    confianza_valor = 0.0

    if len(results.boxes) > 0:
        box = results.boxes[0]
        prediccion_nombre = results.names[int(box.cls)]
        confianza_valor = float(box.conf)
        respuesta_agente = agente_inteligente_llm(prediccion_nombre, confianza_valor)
    else:
        respuesta_agente = "No veo nada claro aquí. ¿Puedes acercar más la cámara?"


    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    ext = file.filename.split(".")[-1]
    nombre_unico = f"img_{timestamp}.{ext}"

    
    if not os.path.exists("imagenes_subidas"):
        os.makedirs("imagenes_subidas")
    
    ruta_archivo = f"imagenes_subidas/{nombre_unico}"
    with open(ruta_archivo, "wb") as buffer:
        buffer.write(contents)

    nueva_imagen = modelsProyecto.Imagen(
        name=nombre_unico,
        ruta=ruta_archivo,
        usuario_id=usuario.id,
        prediccion=prediccion_nombre,
        confianza=confianza_valor
    )
    db.add(nueva_imagen)
    
    nuevo_historial = modelsProyecto.HistorialChat(
        usuario_id=usuario.id,
        mensaje_usuario=f"Detección de {prediccion_nombre}",
        respuesta_agente=respuesta_agente
    )
    db.add(nuevo_historial)
    db.commit()
    
    im_array = results.plot() 
    im_rgb = Image.fromarray(im_array[..., ::-1])
    
    img_io = io.BytesIO()
    im_rgb.save(img_io, 'JPEG', quality=70)
    img_io.seek(0)
    return StreamingResponse(
        img_io, 
        media_type="image/jpeg",
        headers={
            "X-Agent-Reply": respuesta_agente.replace("\n", " | "), 
            "X-Detection": prediccion_nombre
        }
    )

@app.get("/historial", 
    summary="Obtener historial de chat",
    description="Recupera las últimas 10 consultas del usuario autenticado.")
async def obtener_mi_historial(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    usuario = db.query(modelsProyecto.Usuario).filter(modelsProyecto.Usuario.username == username).first()
    
    # Trae los últimos 10 mensajes
    return db.query(modelsProyecto.HistorialChat).filter(
        modelsProyecto.HistorialChat.usuario_id == usuario.id
    ).order_by(modelsProyecto.HistorialChat.fecha.desc()).limit(10).all()


@app.delete("/historial", 
    summary="Vaciar historial",
    description="Borra permanentemente todo el historial del usuari.")
async def vaciar_todo_el_historial(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload.get("sub")
    usuario = db.query(modelsProyecto.Usuario).filter(modelsProyecto.Usuario.username == username).first()

    registros = db.query(modelsProyecto.HistorialChat).filter(
        modelsProyecto.HistorialChat.usuario_id == usuario.id
    )
    
    cantidad = registros.count()
    registros.delete(synchronize_session=False)
    db.commit()
    
    return {"mensaje": f"Se han eliminado {cantidad} registros de tu historial"}


if __name__ == "__main__":
    uvicorn.run("ProyectoBasura:app", host="127.0.0.1", port=8000, reload=True)