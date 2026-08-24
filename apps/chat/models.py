"""
Models for Chat app
"""
from django.db import models
from django.conf import settings
from django.urls import reverse


class Conversation(models.Model):
    """
    محادثة بين عميل ومقدم خدمة
    """
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer_conversations',
        verbose_name='العميل'
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_conversations',
        verbose_name='مقدم الخدمة'
    )
    service = models.ForeignKey(
        'marketplace.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        verbose_name='الخدمة'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخر تحديث')

    class Meta:
        verbose_name = 'محادثة'
        verbose_name_plural = 'المحادثات'
        ordering = ['-updated_at']
        unique_together = ['customer', 'provider']

    def __str__(self):
        return f"محادثة بين {self.customer.username} و {self.provider.username}"

    def get_absolute_url(self):
        return reverse('chat:conversation_detail', kwargs={'pk': self.pk})

    def get_other_user(self, user):
        """الحصول على المستخدم الآخر في المحادثة"""
        if user == self.customer:
            return self.provider
        return self.customer

    def get_unread_count(self, user):
        """عدد الرسائل غير المقروءة للمستخدم"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()


class Message(models.Model):
    """
    رسالة داخل محادثة
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='المحادثة'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='المرسل'
    )
    content = models.TextField(verbose_name='المحتوى')
    is_read = models.BooleanField(default=False, verbose_name='تم القراءة')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاريخ الإرسال')

    class Meta:
        verbose_name = 'رسالة'
        verbose_name_plural = 'الرسائل'
        ordering = ['created_at']

    def __str__(self):
        return f"رسالة من {self.sender.username} في {self.created_at}"
