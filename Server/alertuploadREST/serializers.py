from rest_framework import serializers
from detection.models import UploadAlert

# Serializer for UploadAlert Model
class UploadAlertSerializer(serializers.ModelSerializer):

    class Meta:
        model = UploadAlert
        fields = ('pk', 'image', 'userID', 'location', 'dateCreated', 'alertReceiver')