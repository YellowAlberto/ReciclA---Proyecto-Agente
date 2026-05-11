import gradio as gr
import requests
import io
from PIL import Image
import re
import base64

# URL interna de la API
API_URL = "http://127.0.0.1:8000"

# --- Imagenes --- 
def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    except Exception:
        return ""

nombre_archivo = "protection-environment-robot-holding-lightbulb-with-recycle-icon-sustainable-and-nature_10461459.jpg!sw800"
img_base64 = get_base64_image(nombre_archivo)

robot_html = f"<img src='data:image/jpeg;base64,{img_base64}' width='40' style='display:inline-block; vertical-align:middle; border-radius:50%; margin-right:10px;'>"
# --- Estilos ---
custom_css = """
#titulo-proyecto h1, #respuesta-agente h2 {
    font-family: 'Charter', 'Bitstream Charter', 'Cambria', 'Georgia', serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.5px !important;
    color: #F3F4F6 !important; /* El color blanco hueso que elegiste */
}
#respuesta-agente p {
    font-family: 'Charter', 'Georgia', serif !important;
    font-size: 1.1em;
}
#btn-actualizar {
    background: #2D5A27 !important;
    color: white !important;
    border: none !important;
}
#btn-actualizar:hover {
    background: #3e7a36 !important;
}
"""

# --- FUNCIONES ---

def registrar_usuario(new_user, new_pass):
    if not new_user or not new_pass:
        return " Por favor, rellena ambos campos.", gr.update()
    try:
        data = {"username": new_user, "password": new_pass}
        response = requests.post(f"{API_URL}/registrar", data=data)
        
        if response.ok: 
            return f" Usuario '{new_user}' registrado. ¡Inicia sesión!", gr.Tabs(selected=1)
        
        error_msg = response.json().get('detail', 'No se pudo registrar')
        return f" Error: {error_msg}", gr.update()
        
    except Exception as e:
        return f" Error de conexión: {str(e)}", gr.update()

def login_usuario(username, password):
    if not username or not password:
        return None, " Introduce tus credenciales.", gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
    try:
        login_data = {"username": username, "password": password}
        res = requests.post(f"{API_URL}/login", data=login_data)
        if res.ok:
            token = res.json().get("access_token")
            user_txt = f" **Usuario:** {username}"
            return token, f" Hola {username}", gr.Tabs(selected=2), user_txt, user_txt, user_txt, user_txt, gr.update(visible=False), gr.update(visible=True), " Preparado para analizar imágenes"
        return None, " Error", gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
    except Exception as e:
        return None, f" Error: {str(e)}", gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

def analizar_foto(token, imagen):
    if not token: return " Debes iniciar sesión primero.", None, gr.Tabs(selected=1)
    if imagen is None: return " Por favor, sube una foto.", None, gr.update()
    try:
        buf = io.BytesIO()
        imagen.save(buf, format="JPEG")
        buf.seek(0)
        headers = {"Authorization": f"Bearer {token}"}
        files = {"file": ("image.jpg", buf, "image/jpeg")}
        res = requests.post(f"{API_URL}/detectar-visual", headers=headers, files=files)
        if res.ok:
            msg_crudo = res.headers.get("X-Agent-Reply", "Sin respuesta")
            det = res.headers.get("X-Detection", "Desconocido")
            msg_formateado = msg_crudo.replace("|", "\n\n")
            msg_formateado = re.sub(r' +', ' ', msg_formateado).strip()
            img_res = Image.open(io.BytesIO(res.content))
            return f"## {robot_html} ReciclA Dice:\n\n{msg_formateado}\n\n**Objeto:** {det}", img_res, gr.update()
        return f" Error: {res.text}", None, gr.update()
    except Exception as e: return f" Error: {str(e)}", None, gr.update()

def ver_historial(token):
    if not token: return " Inicia sesión primero.", gr.Tabs(selected=1)
    try:
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.get(f"{API_URL}/historial", headers=headers)
        if res.ok:
            h = res.json()
            if not h: return "Aún no tienes historial.", gr.update()
            texto = "### Tu historial de reciclaje:\n"
            for item in h:
                fecha = item.get('fecha', 'Sin fecha')[:10]
                resp = item.get('respuesta_agente', 'Sin respuesta')
                texto += f"**{fecha}**:\n> {robot_html} {resp}\n\n--- \n"
            return texto, gr.update()
        return f" Error: {res.text}", gr.update()
    except Exception as e: return f" Error: {str(e)}", gr.update()

def logout_usuario():
    no_user = " **Usuario:** No identificado"
    return None, "Sesión cerrada.", gr.Tabs(selected=1), no_user, no_user, no_user, no_user, gr.update(visible=True), gr.update(visible=False)

def update_usuario(token, nuevo_nombre):
    no_user = " **Usuario:** No identificado"
    if not token or not nuevo_nombre:
        return token, " Error: Datos incompletos", gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
    try:
        headers = {"Authorization": f"Bearer {token}"}
        nuevo_nombre = nuevo_nombre.strip()
        res = requests.put(f"{API_URL}/usuarios/actualizarUsuario?nuevo_username={nuevo_nombre}", headers=headers)
        if res.ok:
            mensaje_exito = f" Nombre cambiado a '{nuevo_nombre}'. Reinicia sesión por seguridad."
            return None, mensaje_exito, gr.Tabs(selected=1), no_user, no_user, no_user, no_user, gr.update(visible=True), gr.update(visible=False)
        error_api = res.json().get('detail', 'Error desconocido')
        return token, f" Error: {error_api}", gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
    except Exception as e:
        return token, f" Error de conexion: {str(e)}", gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

def vaciar_historial_usuario(token):
    if not token: return " Inicia sesión primero."
    headers = {"Authorization": f"Bearer {token}"}
    res = requests.delete(f"{API_URL}/historial", headers=headers)
    return " Historial vaciado correctamente." if res.ok else f" Error: {res.text}"

# --- INTERFAZ ---

with gr.Blocks(title="ReciclA", css=custom_css) as demo: 
    token_state = gr.State()
    gr.Markdown(f"# {robot_html} ReciclA : Tu Asistente Inteligente de Reciclaje", elem_id="titulo-proyecto")
    
    with gr.Tabs() as main_tabs:
        
        # PESTAÑA 0: REGISTRO
        with gr.TabItem("📝 Registro", id=0) as tab_registro:
            user_info_0 = gr.Markdown(" **Usuario:** No identificado")
            gr.Markdown("---")
            reg_user = gr.Textbox(label="Usuario")
            reg_pass = gr.Textbox(label="Contraseña", type="password")
            reg_btn = gr.Button("Registrarme")
            reg_out = gr.Markdown()

        # PESTAÑA 4: PERFIL 
        with gr.TabItem("👤 Mi Perfil", id=4, visible=False) as tab_perfil:
            user_info_p = gr.Markdown(" **Usuario:** No identificado")
            with gr.Group():
                gr.Markdown("### Configuración de Perfil")
                nuevo_nombre_input = gr.Textbox(label="Nuevo nombre de usuario", placeholder="Escribe tu nuevo nombre aquí...")
                btn_cambiar_nombre = gr.Button("Actualizar Nombre", variant="primary", elem_id="btn-actualizar")
                gr.Markdown("<center><small> Por seguridad, se cerrará la sesión tras el cambio.</small></center>")
            logout_btn = gr.Button("Cerrar Sesión", variant="stop")

        # PESTAÑA 1: LOGIN
        with gr.TabItem("🔐 Login", id=1):
            user_info_1 = gr.Markdown(" **Usuario:** No identificado")
            gr.Markdown("---")
            l_user = gr.Textbox(label="Usuario")
            l_pass = gr.Textbox(label="Contraseña", type="password")
            with gr.Row():
                l_btn = gr.Button("Iniciar Sesión", variant="primary")
            l_status = gr.Markdown(visible=False)

        # PESTAÑA 2: ANALISIS
        with gr.TabItem("🔍 Análisis", id=2):
            user_info_2 = gr.Markdown(" **Usuario:** No identificado")
            gr.Markdown("---")
            img_input = gr.Image(type="pil", show_label=False)
            btn_scan = gr.Button("Analizar", variant="primary")
            txt_output = gr.Markdown("Inicia sesión para poder analizar tus imagenes", elem_id="respuesta-agente")
            img_output = gr.Image(show_label=False)

        # PESTAÑA 3: HISTORIAL
        with gr.TabItem("📜 Historial", id=3):
            user_info_3 = gr.Markdown(" **Usuario:** No identificado")
            gr.Markdown("---")
            with gr.Row():
                btn_hist = gr.Button(" Cargar mi Historial", variant="primary")
                btn_vaciar = gr.Button(" Vaciar Historial", variant="stop")
            out_hist = gr.Markdown("Dale a 'Cargar' para ver tus movimientos.")
    
    # --- Botones ---
    reg_btn.click(registrar_usuario, [reg_user, reg_pass], [reg_out, main_tabs])
    
    l_btn.click(
        login_usuario, 
        [l_user, l_pass], 
        [token_state, l_status, main_tabs, user_info_0, user_info_1, user_info_2, user_info_3, tab_registro, tab_perfil]
    )
    
    logout_btn.click(
        logout_usuario,
        None,
        [token_state, l_status, main_tabs, user_info_0, user_info_1, user_info_2, user_info_3, tab_registro, tab_perfil]
    )

    btn_scan.click(analizar_foto, [token_state, img_input], [txt_output, img_output, main_tabs])
    btn_hist.click(ver_historial, [token_state], [out_hist, main_tabs])
    btn_vaciar.click(vaciar_historial_usuario, [token_state], [out_hist])

    btn_cambiar_nombre.click(
        fn=update_usuario,
        inputs=[token_state, nuevo_nombre_input],
        outputs=[token_state, l_status, main_tabs, user_info_0, user_info_1, user_info_2, user_info_3, tab_registro, tab_perfil]
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0", 
        server_port=7860, 
        theme=gr.themes.Soft(),
        favicon_path="favicon.png",
        allowed_paths=["/app"]
    )