import os
import uuid
from django.db import models

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from django.contrib.auth.models import User
from webdev.storage_backends import PublicMediaStorage
from django.conf import settings

# Changes uploaded file name
def scrambleUploadedFilename(instance, filename):
    """
    Scramble / uglify the filename of the uploaded file, but keep the files extension (e.g., .jpg or .png)
    :param instance:
    :param filename:
    :return:
    """
    extension = filename.split(".")[-1]
    return "{}.{}".format(uuid.uuid4(), extension)

# Data model
class UploadAlert(models.Model):
    image = models.ImageField("Uploaded image", upload_to=scrambleUploadedFilename,storage=PublicMediaStorage())
    userID = models.ForeignKey(Token, on_delete=models.CASCADE)
    alertReceiver = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    dateCreated = models.DateTimeField(auto_now_add=True)

# Generate and save a token each time a user is saved in a database
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


# Web Push: suscripción del navegador asociada a un usuario.
class PushSubscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='push_subscriptions'
    )
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=200)   # clave pública del cliente
    auth = models.CharField(max_length=100)     # secreto de autenticación
    user_agent = models.CharField(max_length=300, blank=True, default='')
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PushSubscription({self.user.username})"