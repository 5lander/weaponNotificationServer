from alertuploadREST.serializers import UploadAlertSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse
from django.core.mail import send_mail
from rest_framework.exceptions import ValidationError

from django.http import JsonResponse

from twilio.rest import Client
from threading import Thread
import re
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
        identify_email_sms(serializer)

    else:
        return JsonResponse({'error':'Unable to process data!'},status=400)

    return Response(request.META.get('HTTP_AUTHORIZATION'))

# Identifies if the user provided an email or a mobile number
def identify_email_sms(serializer):

    if(re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', serializer.data['alertReceiver'])):  
        print("Valid Email")
        send_email(serializer)
    elif re.compile("[+593][0-9]{10}").match(serializer.data['alertReceiver']):
        print("Valid Mobile Number")
        send_sms(serializer)
    else:
        print("Invalid Email or Mobile number")


@start_new_thread
def send_email(serializer):
    send_mail('Weapon Detected!', 
    prepare_alert_message(serializer), 
    'weapondetectionsystemproject@gmail.com',
    [serializer.data['alertReceiver']],
    fail_silently=False,)

# Sends SMS
@start_new_thread
def send_sms(serializer):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(body=prepare_alert_message(serializer),
                                    from_=settings.TWILIO_NUMBER,
                                    to=serializer.data['alertReceiver'])

def prepare_alert_message(serializer):
    uuid_with_slashes = split(serializer.data['image'], ".")
    uuid = split(uuid_with_slashes[3], "/")

    url = 'https://weapondetectionsystem.onrender.com/alert' + uuid[2]

    return 'Weapon Detected! View alert at ' + url

def split(value, key):
    return str(value).split(key) 