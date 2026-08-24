from django.contrib.contenttypes.models import ContentType
from .models import Notification, AuditLog

def notify(recipient, event_type, title, message):
    return Notification.objects.create(recipient=recipient,event_type=event_type,title=title,message=message)

def audit(actor, action, target=None, **metadata):
    ct=obj_id=None
    if target is not None:
        ct=ContentType.objects.get_for_model(target); obj_id=str(target.pk)
    return AuditLog.objects.create(actor=actor,action=action,content_type=ct,object_id=obj_id or '',metadata=metadata)
