from alertuploadREST.serializers import UploadAlertSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.core.mail import send_mail, EmailMultiAlternatives
from rest_framework.exceptions import ValidationError

from django.http import JsonResponse

from twilio.rest import Client
from threading import Thread
import re
import os
from datetime import datetime
from django.conf import settings

def start_new_thread(function):
    def decorator(*args, **kwargs):
        t = Thread(target = function, args=args, kwargs=kwargs)
        t.daemon = True
        t.start()
    return decorator

@api_view(['POST'])
def postAlert(request):
    serializer = UploadAlertSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        print(f"Alerta guardada exitosamente. Datos: {serializer.data}")
        identify_email_sms(serializer)
        # 🔔 Notificación Web Push al dueño de la alerta (en segundo plano)
        send_web_push(serializer.instance)

    else:
        print(f"La validación del serializador falló: {serializer.errors}")
        return JsonResponse({'error':'¡No se pudieron procesar los datos!'},status=400)

    return Response(request.META.get('HTTP_AUTHORIZATION'))

# Envía la notificación web push sin bloquear la respuesta HTTP
@start_new_thread
def send_web_push(alert_instance):
    try:
        from detection.webpush_sender import notify_alert_owner
        notify_alert_owner(alert_instance)
    except Exception as e:
        print(f"Error al enviar notificación web push: {e}")

# Identifica si el usuario proporcionó un correo electrónico o un número de teléfono
def identify_email_sms(serializer):
    receiver = serializer.data['alertReceiver']
    image_path = serializer.data.get('image', 'Sin ruta de imagen')
    
    print(f"Procesando alerta para el receptor: {receiver}")
    print(f"Ruta de imagen: {image_path}")

    if(re.search('r^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', receiver)):  
        print("Correo electrónico válido - Enviando correo vía SendGrid...")
        send_enhanced_email(serializer)
    elif re.compile("[+593][0-9]{10}").match(receiver):
        print("Número de teléfono válido - Enviando SMS...")
        send_sms(serializer)
    else:
        print(f"Correo electrónico o número de teléfono inválido: {receiver}")

@start_new_thread
def send_enhanced_email(serializer):
    try:
        print("Iniciando proceso de envío de correo mejorado vía SendGrid...")
        
        # Extraer datos del serializador
        alert_data = extract_alert_data(serializer)
        
        # Crear el correo con HTML
        subject = f"🚨 ALERTA DE SEGURIDAD - Arma Detectada"
        
        # Texto plano como respaldo
        text_content = create_text_email(alert_data)
        
        # Contenido HTML mejorado
        html_content = create_html_email(alert_data)
        
        # Crear correo multipart
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[serializer.data['alertReceiver']]
        )
        
        # Adjuntar versión HTML
        email.attach_alternative(html_content, "text/html")
        
        print(f"Detalles del correo:")
        print(f"  Asunto: {subject}")
        print(f"  Para: {serializer.data['alertReceiver']}")
        print(f"  De: {settings.DEFAULT_FROM_EMAIL}")
        print(f"  Longitud de contenido HTML: {len(html_content)} caracteres")
        
        # Enviar correo vía SendGrid
        result = email.send(fail_silently=False)
        
        print(f"Resultado del envío: {result}")
        if result == 1:
            print("✅ Correo mejorado enviado exitosamente vía SendGrid!")
        else:
            print("Falló el envío del correo - sin error pero el resultado fue 0")
            
    except Exception as e:
        print(f"Error al enviar correo mejorado: {e}")
        import traceback
        print(f"Rastreo completo: {traceback.format_exc()}")
        
        # Respaldo al correo simple
        print("Intentando respaldo a correo simple...")
        send_simple_email_fallback(serializer)

@start_new_thread
def send_simple_email_fallback(serializer):
    """Respaldo al método original si el correo HTML falla"""
    try:
        alert_data = extract_alert_data(serializer)
        
        result = send_mail(
            subject='🚨 Alerta de Seguridad - Arma Detectada',
            message=create_text_email(alert_data),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[serializer.data['alertReceiver']],
            fail_silently=False,
        )
        
        print(f"Resultado de correo de respaldo vía SendGrid: {result}")
        
    except Exception as e:
        print(f"Error en correo de respaldo: {e}")

def extract_alert_data(serializer):
    data = serializer.data
    
    # Obtener URL de la alerta
    alert_url = generate_alert_url(data.get('image', ''))
    
    # Obtener timestamp actual
    current_time = datetime.now()
    
    # Determinar ubicación si está disponible
    location = data.get('location', 'Ubicación no especificada')
    
    # Obtener detalles adicionales
    confidence = data.get('confidence', 'No especificada')
    alert_id = getattr(serializer.instance, 'id', 'N/A') if serializer.instance else 'N/A'
    
    return {
        'alert_url': alert_url,
        'timestamp': current_time,
        'location': location,
        'confidence': confidence,
        'alert_id': alert_id,
        'receiver': data['alertReceiver']
    }

def create_text_email(alert_data):
    text_template = f"""
🚨 ALERTA DE SEGURIDAD CRÍTICA 🚨

Se ha detectado un ARMA en el sistema de vigilancia.

📊 DETALLES DE LA ALERTA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• ID de Alerta: {alert_data['alert_id']}
• Fecha y Hora: {alert_data['timestamp'].strftime('%d/%m/%Y a las %H:%M:%S')}
• Ubicación: {alert_data['location']}
• Nivel de Confianza: {alert_data['confidence']}

🔗 ACCIONES REQUERIDAS:
• Revise inmediatamente la alerta en: {alert_data['alert_url']}
• Verifique el área indicada
• Contacte a las autoridades si es necesario

⚠️ IMPORTANTE: Esta es una alerta automatizada del sistema de detección de armas. 
Tome las medidas de seguridad apropiadas de inmediato.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sistema de Detección de Armas
Generado automáticamente el {alert_data['timestamp'].strftime('%d/%m/%Y a las %H:%M:%S')}
"""
    return text_template.strip()

def create_html_email(alert_data):
    html_template = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alerta de Seguridad</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #dc3545, #c82333);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }}
        .alert-icon {{
            font-size: 48px;
            margin-bottom: 10px;
        }}
        .content {{
            padding: 30px;
        }}
        .alert-details {{
            background-color: #f8f9fa;
            border-left: 5px solid #dc3545;
            padding: 20px;
            margin: 20px 0;
            border-radius: 0 5px 5px 0;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #e9ecef;
        }}
        .detail-row:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: bold;
            color: #495057;
        }}
        .detail-value {{
            color: #212529;
        }}
        .action-button {{
            display: inline-block;
            background: linear-gradient(135deg, #007bff, #0056b3);
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
            margin: 20px 0;
            text-align: center;
            transition: all 0.3s ease;
        }}
        .action-button:hover {{
            background: linear-gradient(135deg, #0056b3, #004085);
            transform: translateY(-2px);
        }}
        .warning-box {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 5px;
            padding: 15px;
            margin: 20px 0;
        }}
        .warning-text {{
            color: #856404;
            font-weight: 500;
        }}
        .footer {{
            background-color: #343a40;
            color: #ffffff;
            padding: 20px;
            text-align: center;
            font-size: 12px;
        }}
        .priority-high {{
            color: #dc3545;
            font-weight: bold;
            font-size: 18px;
        }}
        .timestamp {{
            color: #6c757d;
            font-size: 14px;
        }}
        @media (max-width: 600px) {{
            .container {{
                margin: 10px;
                border-radius: 0;
            }}
            .detail-row {{
                flex-direction: column;
            }}
            .detail-label {{
                margin-bottom: 5px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="alert-icon">🚨</div>
            <h1>ALERTA DE SEGURIDAD CRÍTICA</h1>
            <p style="margin: 10px 0 0 0; font-size: 18px;">Detección de Arma en el Sistema</p>
        </div>
        
        <div class="content">
            <div class="priority-high">⚠️ PRIORIDAD ALTA - ACCIÓN INMEDIATA REQUERIDA</div>
            
            <p>Se ha detectado la presencia de un <strong>arma</strong> en el sistema de vigilancia automatizado. Esta alerta requiere atención inmediata.</p>
            
            <div class="alert-details">
                <h3 style="margin-top: 0; color: #dc3545;">📊 Detalles de la Alerta</h3>
                
                <div class="detail-row">
                    <span class="detail-label">🆔 ID de Alerta:</span>
                    <span class="detail-value">{alert_data['alert_id']}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">🕐 Fecha y Hora:</span>
                    <span class="detail-value">{alert_data['timestamp'].strftime('%d/%m/%Y a las %H:%M:%S')}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">📍 Ubicación:</span>
                    <span class="detail-value">{alert_data['location']}</span>
                </div>
                
                <div class="detail-row">
                    <span class="detail-label">🎯 Confianza:</span>
                    <span class="detail-value">{alert_data['confidence']}</span>
                </div>
                
            </div>
            
            <div style="text-align: center;">
                <a href="{alert_data['alert_url']}" class="action-button">
                    🔍 Ver Detalles de la Alerta
                </a>
            </div>
            
            <div class="warning-box">
                <div class="warning-text">
                    <strong>⚠️ Instrucciones de Seguridad:</strong><br>
                    • Revise inmediatamente la ubicación indicada<br>
                    • Mantenga la calma y siga los protocolos de seguridad<br>
                    • Contacte a las autoridades competentes si es necesario<br>
                    • No se acerque al área hasta confirmar que es segura
                </div>
            </div>
            
            <p><strong>Nota:</strong> Esta es una alerta automatizada generada por el sistema de inteligencia artificial de detección de armas. El sistema ha sido entrenado para identificar amenazas potenciales con alta precisión.</p>
        </div>
        
        <div class="footer">
            <div>🛡️ <strong>Sistema de Detección de Armas</strong></div>
            <div class="timestamp">Generado automáticamente el {alert_data['timestamp'].strftime('%d/%m/%Y a las %H:%M:%S')}</div>
            <div style="margin-top: 10px; font-size: 11px;">
                Este mensaje es confidencial y está destinado únicamente al receptor indicado.
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html_template

# Envía SMS
@start_new_thread
def send_sms(serializer):
    try:
        print("Iniciando proceso de envío de SMS...")
        alert_data = extract_alert_data(serializer)
        
        # Mensaje SMS mejorado pero conciso
        sms_message = f"""🚨 ALERTA SEGURIDAD
Arma detectada - {alert_data['timestamp'].strftime('%d/%m %H:%M')}
Ubicación: {alert_data['location']}
Ver: {alert_data['alert_url']}
ID: {alert_data['alert_id']}"""
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        print(f"Detalles del SMS:")
        print(f"  Mensaje: {sms_message}")
        print(f"  De: {settings.TWILIO_NUMBER}")
        print(f"  Para: {serializer.data['alertReceiver']}")

        message = client.messages.create(
            body=sms_message,
            from_=settings.TWILIO_NUMBER,
            to=serializer.data['alertReceiver']
        )
        
        print(f"¡SMS enviado exitosamente! SID: {message.sid}")
        
    except Exception as e:
        print(f"Error al enviar SMS: {e}")
        import traceback
        print(f"Rastreo completo: {traceback.format_exc()}")

def generate_alert_url(image_path):
    try:
        if not image_path:
            return 'https://weaponnotificationserver.onrender.com/alert/unknown'
        
        # Método robusto usando os.path
        filename = os.path.basename(str(image_path))
        
        if filename:
            name_without_extension = os.path.splitext(filename)[0]
            if name_without_extension:
                return f'https://weaponnotificationserver.onrender.com/alert/{name_without_extension}'
        
        # Respaldo al método original
        parts_by_dot = str(image_path).split(".")
        if len(parts_by_dot) >= 4:
            parts_by_slash = str(parts_by_dot[3]).split("/")
            if len(parts_by_slash) >= 3:
                return f'https://weaponnotificationserver.onrender.com/alert/{parts_by_slash[2]}'
        
        return 'https://weaponnotificationserver.onrender.com/alert/processing'
        
    except Exception as e:
        print(f"Error al generar URL de alerta: {e}")
        return 'https://weaponnotificationserver.onrender.com/alert/error'

def split(value, key):
    return str(value).split(key)