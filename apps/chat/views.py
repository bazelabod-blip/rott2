"""
Views for Chat app
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Max
from django.http import JsonResponse
from .models import Conversation, Message
from .forms import MessageForm
from apps.accounts.models import User


@login_required
def conversation_list(request):
    """قائمة المحادثات للمستخدم الحالي"""
    conversations = Conversation.objects.filter(
        Q(customer=request.user) | Q(provider=request.user)
    ).annotate(
        message_count=Count('messages'),
        last_message_time=Max('messages__created_at')
    ).order_by('-updated_at')
    
    # إضافة معلومات إضافية لكل محادثة
    for conv in conversations:
        conv.other_user = conv.get_other_user(request.user)
        conv.unread_count = conv.get_unread_count(request.user)
        conv.last_message = conv.messages.last()
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'chat/conversation_list.html', context)


@login_required
def conversation_detail(request, pk):
    """تفاصيل محادثة معينة"""
    conversation = get_object_or_404(
        Conversation,
        Q(customer=request.user) | Q(provider=request.user),
        pk=pk
    )
    
    # تحديد الرسائل كمقروءة
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    # معالجة إرسال رسالة جديدة
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.save()
            
            # تحديث وقت المحادثة
            conversation.save()
            
            messages.success(request, 'تم إرسال الرسالة بنجاح')
            return redirect('chat:conversation_detail', pk=pk)
    else:
        form = MessageForm()
    
    context = {
        'conversation': conversation,
        'other_user': conversation.get_other_user(request.user),
        'messages_list': conversation.messages.all(),
        'form': form,
    }
    return render(request, 'chat/conversation_detail.html', context)


@login_required
def start_conversation(request, user_id):
    """بدء محادثة مع مستخدم آخر"""
    other_user = get_object_or_404(User, id=user_id)
    
    # التحقق من أنه ليس نفس المستخدم
    if other_user == request.user:
        messages.error(request, 'لا يمكنك إنشاء محادثة مع نفسك')
        return redirect('chat:conversation_list')
    
    # البحث عن محادثة موجودة
    conversation = Conversation.objects.filter(
        Q(customer=request.user, provider=other_user) |
        Q(customer=other_user, provider=request.user)
    ).first()
    
    # إنشاء محادثة جديدة إذا لم تكن موجودة
    if not conversation:
        # تحديد من هو العميل ومن هو المقدم
        if request.user.is_customer:
            conversation = Conversation.objects.create(
                customer=request.user,
                provider=other_user
            )
        else:
            conversation = Conversation.objects.create(
                customer=other_user,
                provider=request.user
            )
        messages.success(request, 'تم إنشاء المحادثة بنجاح')
    
    return redirect('chat:conversation_detail', pk=conversation.pk)


@login_required
def get_unread_count(request):
    """API لجلب عدد الرسائل غير المقروءة"""
    unread_count = Message.objects.filter(
        Q(conversation__customer=request.user) | Q(conversation__provider=request.user),
        is_read=False
    ).exclude(sender=request.user).count()
    
    return JsonResponse({'unread_count': unread_count})
