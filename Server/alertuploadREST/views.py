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

##prueba para nueva rama 
@api_view(['POST'])
def postAlert(request):
    serializer = UploadAlertSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        print(f"Alert saved successfully. Data: {serializer.data}")
        identify_email_sms(serializer)

    else:
        print(f"Serializer validation failed: {serializer.errors}")
        return JsonResponse({'error':'Unable to process data!'},status=400)

    return Response(request.META.get('HTTP_AUTHORIZATION'))

# Identifies if the user provided an email or a mobile number
def identify_email_sms(serializer):
    receiver = serializer.data['alertReceiver']
    image_path = serializer.data.get('image', 'No image path')
    
    print(f"Processing alert for receiver: {receiver}")
    print(f"Image path: {image_path}")

    if(re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', receiver)):  
        print("Valid Email - Sending email...")
        send_enhanced_email(serializer)
    elif re.compile("[+593][0-9]{10}").match(receiver):
        print("Valid Mobile Number - Sending SMS...")
        send_sms(serializer)
    else:
        print(f"Invalid Email or Mobile number: {receiver}")

@start_new_thread
def send_enhanced_email(serializer):
    try:
        print("Starting enhanced email send process...")
        
        # Extraer datos del serializer
        alert_data = extract_alert_data(serializer)
        
        # Crear el email con HTML
        subject = f"🚨 ALERTA DE SEGURIDAD - Arma Detectada"
        
        # Texto plano como fallback
        text_content = create_text_email(alert_data)
        
        # Contenido HTML mejorado
        html_content = create_html_email(alert_data)
        
        # Crear email multipart
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email='Weapon Detection System <weapondetectionsystemproject@gmail.com>',
            to=[serializer.data['alertReceiver']]
        )
        
        # Adjuntar version HTML
        email.attach_alternative(html_content, "text/html")
        
        print(f"Email details:")
        print(f"  Subject: {subject}")
        print(f"  To: {serializer.data['alertReceiver']}")
        print(f"  HTML content length: {len(html_content)} characters")
        
        # Enviar email
        result = email.send(fail_silently=False)
        
        print(f"Email send result: {result}")
        if result == 1:
            print("Enhanced email sent successfully!")
        else:
            print("Email send failed - no error but result was 0")
            
    except Exception as e:
        print(f"Error sending enhanced email: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        
        # Fallback al email simple
        print("Attempting fallback to simple email...")
        send_simple_email_fallback(serializer)

@start_new_thread
def send_simple_email_fallback(serializer):
    """Fallback al método original si el email HTML falla"""
    try:
        alert_data = extract_alert_data(serializer)
        
        result = send_mail(
            subject='🚨 Alerta de Seguridad - Arma Detectada',
            message=create_text_email(alert_data),
            from_email='weapondetectionsystemproject@gmail.com',
            recipient_list=[serializer.data['alertReceiver']],
            fail_silently=False,
        )
        
        print(f"Fallback email result: {result}")
        
    except Exception as e:
        print(f"Error in fallback email: {e}")

def extract_alert_data(serializer):
    """Extrae y organiza los datos de la alerta"""
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
    """Crea el contenido del email en texto plano"""
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
    """Crea el contenido del email en HTML"""
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
                
                <div class="detail-row">
                    <span class="detail-label">👤 Notificado a:</span>
                    <span class="detail-value">{alert_data['receiver']}</span>
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

# Sends SMS
@start_new_thread
def send_sms(serializer):
    try:
        print("Starting SMS send process...")
        alert_data = extract_alert_data(serializer)
        
        # Mensaje SMS mejorado pero conciso
        sms_message = f"""🚨 ALERTA SEGURIDAD
Arma detectada - {alert_data['timestamp'].strftime('%d/%m %H:%M')}
Ubicación: {alert_data['location']}
Ver: {alert_data['alert_url']}
ID: {alert_data['alert_id']}"""
        
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        print(f"SMS details:")
        print(f"  Message: {sms_message}")
        print(f"  From: {settings.TWILIO_NUMBER}")
        print(f"  To: {serializer.data['alertReceiver']}")

        message = client.messages.create(
            body=sms_message,
            from_=settings.TWILIO_NUMBER,
            to=serializer.data['alertReceiver']
        )
        
        print(f"SMS sent successfully! SID: {message.sid}")
        
    except Exception as e:
        print(f"Error sending SMS: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

def generate_alert_url(image_path):
    """Genera la URL de la alerta de forma robusta"""
    try:
        if not image_path:
            return 'http://127.0.0.1/alert/unknown'
        
        # Método robusto usando os.path
        filename = os.path.basename(str(image_path))
        
        if filename:
            name_without_extension = os.path.splitext(filename)[0]
            if name_without_extension:
                return f'http://127.0.0.1/alert/{name_without_extension}'
        
        # Fallback al método original
        parts_by_dot = str(image_path).split(".")
        if len(parts_by_dot) >= 4:
            parts_by_slash = str(parts_by_dot[3]).split("/")
            if len(parts_by_slash) >= 3:
                return f'http://127.0.0.1/alert/{parts_by_slash[2]}'
        
        return 'http://127.0.0.1/alert/processing'
        
    except Exception as e:
        print(f"Error generating alert URL: {e}")
        return 'http://127.0.0.1/alert/error'

def split(value, key):
    """Función auxiliar para dividir strings"""
    return str(value).split(key)