import resend
import os
from django.conf import settings

# Asegúrate de poner tu API Key en las variables de entorno de Render
resend.api_key = os.getenv("RESEND_API_KEY", "re_EZM6d2Rs_3iWv3G7ymUHvF8iVwPQ4bPDW")

def enviar_correo(asunto, destinatario, contenido_html):
    params = {
        "from": "onboarding@resend.dev", # Resend requiere dominio verificado para usar otro correo
        "to": destinatario,
        "subject": asunto,
        "html": contenido_html,
    }
    return resend.Emails.send(params)