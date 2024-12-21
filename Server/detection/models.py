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