import django_filters
from django_filters import DateFilter, CharFilter

from .models import *

# Filtering
class DetectionFilter(django_filters.FilterSet):

	startDate = DateFilter(field_name="dateCreated", lookup_expr='gte')
	endDate = DateFilter(field_name="dateCreated", lookup_expr='lte')
	location = CharFilter(field_name='location', lookup_expr='icontains')
	alertReceiver = CharFilter(field_name='alertReceiver', lookup_expr='icontains')

	class Meta:
		model = UploadAlert
		fields = '__all__'
		exclude = ['customer', 'userID', 'image', 'uuid']