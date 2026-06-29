from django.contrib import admin

from detection.models import UploadAlert, PushSubscription

# Register your models here.
admin.site.register(UploadAlert)


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'created')
    search_fields = ('user__username', 'endpoint')
    readonly_fields = ('created',)