---
title: Agente Inteligente Reciclaje
emoji: ♻️
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# ReciclA: Asistente Inteligente de Reciclaje

![Sync to Hugging Face](https://github.com/YellowAlberto/ReciclA---Proyecto-Agente/actions/workflows/sync_to_hf.yml/badge.svg)

**ReciclA** es un ecosistema inteligente diseñado para facilitar el reciclaje mediante el uso de Inteligencia Artificial avanzada. El sistema integra visión artificial para la detección de residuos y un agente conversacional que asesora al usuario sobre la gestión de desechos.

### Componentes Clave:

*   **Agente Inteligente:** Implementado con **Groq** para ofrecer respuestas expertas y personalizadas en lenguaje natural.
*   **Visión Artificial:** Utiliza modelos **YOLOv8** optimizados para identificar objetos en imágenes subidas por el usuario.
*   **Base de Datos Híbrida:** Configurada para trabajar con **PostgreSQL (Supabase)** en producción o **SQLite** de forma local y automática si no se detectan credenciales.
*   **Contenedorización:** Sistema orquestado con **Docker Compose** para garantizar la portabilidad sin dependencias manuales.
* **CI/CD Automático:** Sincronización automatizada mediante **GitHub Actions** que despliega cada actualización directamente en **Hugging Face Spaces**.

---

# Instrucciones de Instalación

### Requisitos previos:
*   **Docker Desktop:** Instalado y en funcionamiento.
*   **Groq API Key:** Necesaria para el funcionamiento del agente conversacional.

### Pasos para el despliegue:

1.  **Configuración de entorno:** Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:
    ```env
    GROQ_API_KEY=tu_api_key_aqui
    SECRET_KEY=un_secreto_aleatorio_para_jwt
    # Opcional: Si se omite DATABASE_URL, el sistema iniciará en modo SQLite local
    DATABASE_URL=postgresql://tu_url_de_supabase
    ```

2.  **Lanzamiento:** Abre una terminal en la carpeta del proyecto y ejecuta el siguiente comando:
    ```bash
    docker-compose up --build
    ```

3.  **Acceso a las interfaces:**
    *   **Despliegue Online (Hugging Face):** [https://huggingface.co/spaces/YellowAlberto/ReciclA]
    *   **Frontend (Gradio):** [http://localhost:7860](http://localhost:7860)
    *   **API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)

> **Nota sobre el despliegue:** Este repositorio está configurado con **GitHub Actions**. Cualquier commit en la rama `main` dispara automáticamente una actualización del contenedor en Hugging Face.

---

# Uso de la API

La API sigue los principios **RESTful**, utilizando los verbos HTTP para definir las acciones sobre cada recurso.

| Método | Endpoint | Descripción |
| :--- | :--- | :--- |
| **POST** | `/registrar` | Crea la cuenta de un usuario y lo guarda en la base de datos. |
| **POST** | `/login` | Comprueba las credenciales y genera un token JWT de acceso. |
| **POST** | `/detectar-visual` | Analiza una imagen, devuelve la predicción + respuesta del agente y guarda en historial. |
| **GET** | `/historial` | Recupera las últimas 10 consultas del usuario autenticado. |
| **PUT** | `/usuarios/actualizarUsuario` | Actualiza el nombre de usuario del perfil activo. |
| **DELETE** | `/historial` | Borra permanentemente todo el historial del usuario. |

---

### Persistencia de Datos
El proyecto utiliza **volúmenes de Docker** para asegurar que la persistencia sea efectiva:
*   **SQLite:** Si se usa el modo local, se creará un archivo `test.db` en tu carpeta raíz que no se borrará al apagar el contenedor.
*   **Interfaz:** El logo e iconos se cargan mediante codificación **Base64** para garantizar su visualización correcta sin errores de rutas locales o bloqueos de seguridad del navegador.