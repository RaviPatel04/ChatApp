from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import localtime
from django.http import JsonResponse
from .forms import ContactUSForm
from django.db.models import Q
from django.utils import timezone
from zoneinfo import ZoneInfo
import mimetypes
import logging
import json
import re
import os
from .models import ContactUs, Profile, Message, User, FriendRequest, Friendship, Notification, Group, GroupMessage, GroupRequest, GroupProfile
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from cloudinary.utils import cloudinary_url
from cloudinary.uploader import destroy
from cloudinary.uploader import upload
from cloudinary.exceptions import Error as CloudinaryError




# Create your views here.
def home(request):
    return render(request, "home.html")

def about(request):
    return render(request, "about.html")


def contact(request):
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == "POST":
        form = ContactUSForm(request.POST)
        if form.is_valid():
            contact = ContactUs(
                name = form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                communication_method=form.cleaned_data['communication_method'],
                message=form.cleaned_data['message'],
            )
            contact.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('home')
        else:
            messages.error(request, "Please correct the errors below.")

    else:
        form = ContactUSForm()
    return render(request, "contact.html", {'form': form})



def register_view(request):
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == "POST":
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Password and Confirm Password must be the same.")
            return redirect("register_view")
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!!")
            return redirect("register_view")
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        # messages.success(request, "Account created successfully!!")
        return redirect("login_view")
    
    return render(request, "register_view.html")




def login_view(request):

    if request.method == "POST":
        username_email = request.POST['username_email']
        password = request.POST['password']

        user = None
        if re.match(r"[^@]+@[^@]+\.[^@]+", username_email):
            UserModel = get_user_model()
            try:
                user_obj = UserModel.objects.get(email=username_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except UserModel.DoesNotExist:
                user = None
        else:
            user = authenticate(request, username = username_email, password = password)

        if user is not None:
            login(request, user)
            # messages.success(request, "You have been logged In successfully!!")
            return redirect("chat")
        else:
            messages.error(request, "Invalid username/email or password!!")
            return redirect("login_view")
        
    return render(request, "login_view.html")




def logout_view(request):
    logout(request)
    # messages.success(request, "You have been logged Out successfully!!")
    return redirect("login_view")



@login_required
@require_POST
def update_profile(request):
    ist = ZoneInfo("Asia/Kolkata")
    try:
        profile = request.user.profile
        user = request.user

        new_email = request.POST.get('email', '').strip()
        if new_email and new_email != user.email:
            if User.objects.filter(email=new_email).exclude(id = user.id).exists():
                messages.error(request, "Email already taken!")
                return redirect("chat")
            
            user.email = new_email
            user.save()

        
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        if 'bio' in request.POST:
            profile.bio = request.POST['bio']
        if 'phone' in request.POST:
            profile.phone = request.POST['phone']
            
        profile.save()
        return JsonResponse({"success": True, "message": "Profile updated successfully!"})
    
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=500)




@login_required
def chat(request):
    ist = ZoneInfo("Asia/Kolkata")
    user = request.user

    friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))

    friends = []
    for friendship in friendships:
        friend = friendship.user2 if friendship.user1 == user else friendship.user1  

        # ✅ Fetch the last message between the logged-in user and this friend
        last_message = Message.objects.filter(
            Q(sender=user, receiver=friend) | Q(sender=friend, receiver=user)
        ).order_by("-timestamp").first()

        # ✅ Attach the last message dynamically
        setattr(friend, "last_message", last_message)

        friends.append(friend)

    groups = user.custom_groups.all().order_by('-created_at')    

    for group in groups:
        last_group_message = GroupMessage.objects.filter(group=group).order_by('-timestamp').first()
        setattr(group, "last_message", last_group_message)


    return render(request, "chat.html", {"friends": friends, "groups":groups})





@login_required
def get_messages(request, friend_id):
    friend = get_object_or_404(User, id=friend_id)

    # Convert UTC time to IST before sending to frontend
    ist = ZoneInfo("Asia/Kolkata") 

    # Fetch only messages between the logged-in user and selected friend
    messages = Message.objects.filter(
        Q(sender=request.user, receiver=friend) | 
        Q(sender=friend, receiver=request.user)
    ).order_by("timestamp")

    messages_list = []
    for msg in messages:
        file_url = msg.file.build_url(secure=True) if msg.file else None
        # file_name = msg.file.name if msg.file else None

        # print(f"DEBUG - File URL: {file_url}")  # Check server logs


        if msg.file:
            file_name = msg.file.public_id.split('/')[-1] if msg.file.public_id else "file"
            file_extension = msg.file.format if hasattr(msg.file, 'format') else None

            if file_extension:
                file_type = mimetypes.guess_type(f"dummy.{file_extension}")[0]
            else:
                # Try to get it from the original filename or resource_type
                file_type = msg.file.resource_type if hasattr(msg.file, 'resource_type') else None
                # Map Cloudinary resource types to MIME types
                if file_type == 'image':
                    file_type = 'image/jpeg'  # Default image type
                elif file_type == 'video':
                    file_type = 'video/mp4'   # Default video type
                elif file_type == 'raw' or file_type == 'auto':
                    # For PDF and other documents
                    if file_url and file_url.endswith('.pdf'):
                        file_type = 'application/pdf'
                    else:
                        file_type = 'application/octet-stream'  # Generic binary type
        else:
            file_name = None
            file_type = None
        
        # print(f"DEBUG - File NAME: {file_name}")
        # print(f"DEBUG - File TYPE: {file_type}")


        messages_list.append(
            {
                "id": msg.id,
                "sender": msg.sender.username,
                "receiver": msg.receiver.username,
                "text": msg.text,
                "audio": msg.audio.url if msg.audio else None,  
                "file_url": file_url,
                "file_name": file_name,
                "file_type": file_type, 
                "timestamp": localtime(msg.timestamp).astimezone(ist).strftime("%I:%M %p"),
                "datestamp": localtime(msg.timestamp).astimezone(ist).strftime("%B %d, %Y"),
                "is_sent_by_me": msg.sender == request.user
            }
        )

    return JsonResponse({"messages": messages_list})




@login_required
def send_message(request):

    ist = ZoneInfo("Asia/Kolkata") 

    if request.method == "POST":
        sender = request.user
        receiver_id = request.POST.get("receiver_id")
        text = request.POST.get("text").strip()

        if not receiver_id or not text:
            return JsonResponse({"success": False, "error": "Message cannot be empty"}, status=400)

        receiver = get_object_or_404(User, id=receiver_id)

        # Save message to database
        message = Message.objects.create(sender=sender, receiver=receiver, text=text)

        return JsonResponse({
            "success": True,
            "message": {
                "id": message.id,
                "sender": message.sender.username,
                "receiver": message.receiver.username,
                "text": message.text,
                "timestamp": localtime(message.timestamp).astimezone(ist).strftime("%I:%M %p"),
                "datestamp": localtime(message.timestamp).astimezone(ist).strftime("%B %d, %Y"),
                "is_sent_by_me": True
            }
        })
    
    return JsonResponse({"success": False}, status=400)





@login_required
def get_user_profile(request, user_id):
    ist = ZoneInfo("Asia/Kolkata")
    user = get_object_or_404(User, id=user_id)
    profile = user.profile

    return JsonResponse({
        "username": user.username,
        "avatar": profile.avatar.url if profile.avatar else "/avatars/default.png",
        "bio": profile.bio,
        "email":user.email
    })




@login_required
def send_voice_message(request):
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == "POST" and request.FILES.get("voice_message"):
        sender = request.user
        voice_file = request.FILES["voice_message"]
        group_id = request.POST.get("group_id")
        receiver_id = request.POST.get("receiver_id")

        
        folder_path = "voice_messages"
        if group_id:
            folder_path = "group_voice_messages"

        try:
            upload_result = upload(
                voice_file,
                resource_type="video",  # required for audio/webm
                folder=folder_path
            )
        except CloudinaryError as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)


        # ✅ Handle Group Voice Message
        if group_id:
            group = get_object_or_404(Group, id=group_id)
            message = GroupMessage.objects.create(sender=sender, group=group, audio=upload_result["secure_url"])

            # return JsonResponse({
            #     "success": True,
            #     "message": {
            #         "id": message.id,
            #         "audio": message.audio.url,
            #         "timestamp": localtime(message.timestamp).astimezone(ist).strftime("%I:%M %p"),
            #         "datestamp": localtime(message.timestamp).astimezone(ist).strftime("%B %d, %Y"),
            #         "is_sent_by_me": True
            #     }
            # })
        # ✅ Handle Friend Voice Message
        elif receiver_id:
            receiver = get_object_or_404(User, id=receiver_id)
            message = Message.objects.create(sender=sender, receiver=receiver, audio=upload_result["secure_url"])

            # return JsonResponse({
            #     "success": True,
            #     "message": {
            #         "id": message.id,
            #         "audio": message.audio.url,
            #         "timestamp": localtime(message.timestamp).astimezone(ist).strftime("%I:%M %p"),
            #         "datestamp": localtime(message.timestamp).astimezone(ist).strftime("%B %d, %Y"),
            #         "is_sent_by_me": True
            #     }
            # })
        else:
            return JsonResponse({"success": False, "error": "No valid recipient provided"}, status=400)
        
        return JsonResponse({
            "success": True,
            "message": {
                "id": message.id,
                "audio": message.audio,
                "timestamp": localtime(message.timestamp).astimezone(ist).strftime("%I:%M %p"),
                "datestamp": localtime(message.timestamp).astimezone(ist).strftime("%B %d, %Y"),
                "is_sent_by_me": True
            }
        })
    
    return JsonResponse({"success": False}, status=400)



@login_required
def send_attachment(request):
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == "POST":
        sender = request.user
        receiver_id = request.POST.get("receiver_id")
        group_id = request.POST.get("group_id")
        file = request.FILES.get("attachment")


        if not file:
            return JsonResponse({"success": False, "error": "No file uploaded"}, status=400)
        
        if receiver_id:
            # Handle direct message
            receiver = get_object_or_404(User, id=receiver_id)
            message = Message.objects.create(sender=sender, receiver=receiver, file=file)

            file_url = message.file.build_url(secure=True) if message.file else None

            # print(f"DEBUG - File URL: {file_url}")

            if message.file:
                file_name = message.file.public_id.split('/')[-1] if message.file.public_id else "file"
            else:
                file_name = None
            if file_url and file_name:
                file_extension = file_name.split('.')[-1] if '.' in file_name else ''
                file_type = mimetypes.guess_type(f"dummy.{file_extension}")[0] if file_extension else None
            else:
                file_type = None


            response_message = {
                "id": message.id,
                "sender": message.sender.username,
                "receiver": message.receiver.username,
                "file_url": file_url,
                "file_name": file_name,
                "file_type": file_type,
                "timestamp": localtime(message.timestamp).astimezone(ist).strftime("%I:%M %p"),
                "datestamp": localtime(message.timestamp).astimezone(ist).strftime("%B %d, %Y"),
                "is_sent_by_me": True
            }
        elif group_id:
            # Handle group message
            group = get_object_or_404(Group, id=group_id)

            # Ensure sender is part of the group
            if not group.members.filter(id=sender.id).exists():
                return JsonResponse({"success": False, "error": "You are not a member of this group"}, status=403)

            message = GroupMessage.objects.create(sender=sender, group=group, file=file)

            file_url = message.file.build_url(secure=True) if message.file else None

            # print(f"DEBUG - File URL: {file_url}")

            if message.file:
                file_name = message.file.public_id.split('/')[-1] if message.file.public_id else "file"
            else:
                file_name = None
            if file_url and file_name:
                file_extension = file_name.split('.')[-1] if '.' in file_name else ''
                file_type = mimetypes.guess_type(f"dummy.{file_extension}")[0] if file_extension else None
            else:
                file_type = None

            response_message = {
                "id": message.id,
                "sender": message.sender.username,
                "group": message.group.name,
                "file_url": file_url,
                "file_name": file_name,
                "file_type": file_type,
                "timestamp": localtime(message.timestamp).astimezone(ist).strftime("%I:%M %p"),
                "datestamp": localtime(message.timestamp).astimezone(ist).strftime("%B %d, %Y"),
                "is_sent_by_me": True
            }
        else:
            return JsonResponse({"success": False, "error": "No valid recipient provided"}, status=400)
        
        return JsonResponse({"success": True, "message": response_message})
        
    return JsonResponse({"success": False}, status=400)




@login_required
@csrf_exempt
def send_friend_request(request):
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        email = data.get('email')
        
        try:
            receiver = User.objects.get(username=username, email=email)
            
            # Check if user is trying to add themselves
            if receiver == request.user:
                return JsonResponse({'status': 'error', 'message': 'You cannot send a friend request to yourself'})
                
            # Check if already friends
            friendship_exists = Friendship.objects.filter(
                (Q(user1=request.user) & Q(user2=receiver)) | 
                (Q(user1=receiver) & Q(user2=request.user))
            ).exists()
            
            if friendship_exists:
                return JsonResponse({'status': 'error', 'message': 'You are already friends with this user'})
                
            # Check if request already sent
            existing_request = FriendRequest.objects.filter(
                sender=request.user, 
                receiver=receiver
            ).first()
            
            if existing_request:
                if existing_request.status == 'pending':
                    return JsonResponse({'status': 'error', 'message': 'Friend request already sent'})
                elif existing_request.status == 'rejected':
                    # Update the rejected request to pending again
                    existing_request.status = 'pending'
                    existing_request.save()
                    return JsonResponse({'status': 'success', 'message': '🤝Friend request sent Successfully!!'})
            
            # Create new friend request
            FriendRequest.objects.create(
                sender=request.user,
                receiver=receiver,
                status='pending'
            )
            
            return JsonResponse({'status': 'success', 'message': '🤝Friend request sent Successfully!!'})
        
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found or Check Username and Email'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})



@login_required
@csrf_exempt
def handle_friend_request(request):
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == 'POST':
        data = json.loads(request.body)
        request_id = data.get('request_id')
        action = data.get('action')
        
        friend_request = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)
        
        if action == 'accept':
            friend_request.status = 'accepted'
            friend_request.save()
            
            # Find and mark the notification as read
            notification = Notification.objects.filter(
                user=request.user,
                related_request=friend_request,
                type='friend_request'
            ).first()
            
            if notification:
                notification.read = True
                notification.save()
            
            return JsonResponse({'status': 'success', 'message': 'Friend request accepted'})
        
        elif action == 'reject':
            friend_request.status = 'rejected'
            friend_request.save()
            
            # Find and mark the notification as read
            notification = Notification.objects.filter(
                user=request.user,
                related_request=friend_request,
                type='friend_request'
            ).first()
            
            if notification:
                notification.read = True
                notification.save()
            
            return JsonResponse({'status': 'success', 'message': 'Friend request rejected'})
        
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

@login_required
def get_notifications(request):
    ist = ZoneInfo("Asia/Kolkata")
    try:
        ist = ZoneInfo("Asia/Kolkata") 
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        
        # Fetch notifications with related objects
        notifications = Notification.objects.filter(
            user=request.user,
            created_at__gte=seven_days_ago
        ).select_related('sender', 'related_request', 'group_request', 'group_request__group')
        
        unread_count = notifications.filter(read=False).count()
        
        notifications_data = []
        processed_notifications = set()
        
        for notification in notifications[:10]:  # Get the latest 10 notifications
            # Create a unique key for each notification to prevent duplicates
            notification_key = (
                notification.id, 
                notification.type, 
                notification.sender_id, 
                notification.created_at
            )
            
            # Skip if this notification has already been processed
            if notification_key in processed_notifications:
                continue
            
            # Skip notifications for rejected friend requests that are already read
            if notification.type == 'request_rejected' and notification.read:
                continue
            
            # Skip notifications for friend requests that are no longer pending
            if notification.related_request and notification.type == 'friend_request':
                if notification.related_request.status != 'pending':
                    # If the request is no longer pending and the notification is read, skip it
                    if notification.read:
                        continue
            
            # Prepare base notification info
            notification_info = {
                'id': notification.id,
                'type': notification.type,
                'sender_username': notification.sender.username,
                'created_at': notification.created_at.astimezone(ist).strftime('%d-%m-%Y %H:%M'),
                'read': notification.read,
            }
            
            # Handle group-related notifications
            if notification.type in ['group_invite', 'group_invite_accepted', 'group_invite_rejected']:
                # Try multiple ways to get group name
                group_name = None
                
                # Check extra_data first
                if notification.extra_data:
                    try:
                        extra_data = json.loads(notification.extra_data)
                        group_name = extra_data.get('group_name')
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                # Fallback to group_request
                if not group_name and notification.group_request:
                    try:
                        group_name = notification.group_request.group.name
                    except AttributeError:
                        pass
                
                # Add group name if found
                if group_name:
                    notification_info['group_name'] = group_name
                
                # Add group request ID
                if notification.group_request:
                    notification_info['group_request_id'] = notification.group_request.id
            
            # Handle friend request-related notifications
            if notification.related_request:
                notification_info['request_id'] = notification.related_request.id
            
            # Add to notifications data and mark as processed
            notifications_data.append(notification_info)
            processed_notifications.add(notification_key)
        
        return JsonResponse({
            'notifications': notifications_data,
            'unread_count': unread_count
        })
    
    except Exception as exc:
        logger.exception(f"Unexpected error in get_notifications: {exc}")
        return JsonResponse({
            'success': False, 
            'message': 'Unexpected server error', 
            'error': str(exc)
        }, status=500)
    


@login_required
@csrf_exempt
def mark_notification_read(request, notification_id):
    ist = ZoneInfo("Asia/Kolkata")
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return JsonResponse({'status': 'success'})



@login_required
@csrf_exempt
def delete_notification(request, notification_id):
    ist = ZoneInfo("Asia/Kolkata")
    """Completely delete a notification from the database"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.delete()
    return JsonResponse({'status': 'success'})



@login_required
def get_friends(request):
    ist = ZoneInfo("Asia/Kolkata")
    # Get all friendships where the current user is involved
    friendships = Friendship.objects.filter(
        Q(user1=request.user) | Q(user2=request.user)
    ).select_related('user1', 'user2')
    
    friends = []
    for friendship in friendships:
        friend = friendship.user2 if friendship.user1 == request.user else friendship.user1
        friends.append({
            'id': friend.id,
            'username': friend.username,
            'email': friend.email,
        })
    
    return JsonResponse({'friends': friends})


@login_required
def get_notification_count(request):
    ist = ZoneInfo("Asia/Kolkata")
    """Get only the unread notification count for the current user"""
    unread_count = Notification.objects.filter(user=request.user, read=False).count()
    return JsonResponse({'unread_count': unread_count})




@login_required
@csrf_exempt
def create_group(request):
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == "POST":
        data = json.loads(request.body.decode('utf-8'))
        group_name = data.get('group_name','').strip()

        if not group_name:
            return JsonResponse({'success': False, 'message': 'Group name is required.'})
        
        group = Group.objects.create(name = group_name, admin = request.user)

        group.members.add(request.user)

        return JsonResponse({'success': True, 'message': 'Group created successfully!'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)


@login_required
def get_group_messages(request, group_id):
    group = get_object_or_404(Group, id=group_id)
        
    ist = ZoneInfo("Asia/Kolkata") 

    
    if not group.members.filter(id=request.user.id).exists():
        return JsonResponse({"messages": []})

    messages_qs = GroupMessage.objects.filter(group=group).order_by("timestamp")
    messages_list = []

    for msg in messages_qs:
        file_url = msg.file.build_url(secure=True) if msg.file else None
        # file_name = msg.file.name if msg.file else None

        # print(f"DEBUG - File URL: {file_url}")


        if msg.file:
            file_name = msg.file.public_id.split('/')[-1] if msg.file.public_id else "file"
            file_extension = msg.file.format if hasattr(msg.file, 'format') else None

            if file_extension:
                file_type = mimetypes.guess_type(f"dummy.{file_extension}")[0]
            else:
                # Try to get it from the original filename or resource_type
                file_type = msg.file.resource_type if hasattr(msg.file, 'resource_type') else None
                # Map Cloudinary resource types to MIME types
                if file_type == 'image':
                    file_type = 'image/jpeg'  # Default image type
                elif file_type == 'video':
                    file_type = 'video/mp4'   # Default video type
                elif file_type == 'raw' or file_type == 'auto':
                    # For PDF and other documents
                    if file_url and file_url.endswith('.pdf'):
                        file_type = 'application/pdf'
                    else:
                        file_type = 'application/octet-stream'  # Generic binary type
        else:
            file_name = None
            file_type = None
        
        # print(f"DEBUG - File NAME: {file_name}")
        # print(f"DEBUG - File TYPE: {file_type}")


        
    
        # ✅ Get sender avatar (Assuming avatar is stored in `profile.avatar.url`)
        sender_avatar = (
            msg.sender.profile.avatar.url
            if hasattr(msg.sender, "profile") and msg.sender.profile.avatar
            else "/avatar/group_default.png"
        )

        messages_list.append({
            "id": msg.id,
            "sender": msg.sender.username,
            "sender_avatar": sender_avatar,  # ✅ Sends sender avatar
            "text": msg.text or "",
            "audio": msg.audio.url if msg.audio else None,
            "file_url": file_url,
            "file_name": file_name,
            "file_type": file_type,
            "timestamp": localtime(msg.timestamp).astimezone(ist).strftime("%I:%M %p"),
            "datestamp": localtime(msg.timestamp).astimezone(ist).strftime("%B %d, %Y"),
            "is_sent_by_me": (msg.sender == request.user),
        })
    return JsonResponse({"messages": messages_list})


@login_required
@csrf_exempt
def send_group_message(request):

    ist = ZoneInfo("Asia/Kolkata")
    
    if request.method == "POST":
        sender = request.user
        data = json.loads(request.body.decode("utf-8"))
        group_id = data.get("group_id")
        text = data.get("text", "").strip()

        if not group_id or not text:
            return JsonResponse({"success": False, "error": "Message cannot be empty"}, status=400)

        group = get_object_or_404(Group, id=group_id)
        if sender not in group.members.all():
            return JsonResponse({"success": False, "error": "You are not a member of this group"}, status=403)

        message = GroupMessage.objects.create(group=group, sender=sender, text=text)

        return JsonResponse({
            "success": True,
            "message": {
                "id": message.id,
                "sender": message.sender.username,
                # "receiver": message.receiver.username,
                "text": message.text,
                "timestamp": localtime(message.timestamp).astimezone(ist).strftime("%I:%M %p"),
                "datestamp": localtime(message.timestamp).astimezone(ist).strftime("%B %d, %Y"),
                "is_sent_by_me": True
            }
        })
    return JsonResponse({"success": False, "error": "Invalid method"}, status=400)



@login_required
@csrf_exempt
def handle_group_invite(request):
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        notification_id = data.get('notification_id')
        action = data.get('action')  # "accept" or "reject"

        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        if notification.type != 'group_invite':
            return JsonResponse({'success': False, 'message': 'Not a group invite.'})

        group = notification.group_request.group
        group_name = group.name

        # print(f"Group Name:----------------- {group_name}")

        if action == 'accept':
            group.members.add(request.user)
            # Mark notification as read or delete it
            notification.read = True
            notification.save()
            # Possibly create a new 'group_invite_accepted' notification
            
            Notification.objects.create(
                user=notification.sender,
                sender=request.user,
                type='group_invite_accepted',
                read=False
            )
            return JsonResponse({'success': True, 'message': 'You have joined the group.'})

        elif action == 'reject':
            notification.read = True
            notification.save()
            # Possibly create 'group_invite_rejected' for the admin
            Notification.objects.create(
                user=notification.sender,
                sender=request.user,
                type='group_invite_rejected',
                read=False
            )
            return JsonResponse({'success': True, 'message': 'You have rejected the group invite.'})

    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=400)





@login_required
@csrf_exempt
def send_group_invite(request):
    """
    Group admin sends an invitation to a user to join a group.
    Expects JSON with keys: group_id, username, email.
    """
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        group_id = data.get('group_id')
        username = data.get('username')
        email = data.get('email')

        if not group_id or not username or not email:
            return JsonResponse({'success': False, 'message': 'Missing fields.'})
        
        group = get_object_or_404(Group, id=group_id)
        # Ensure the current user is the admin of the group.
        if group.admin != request.user:
            return JsonResponse({'success': False, 'message': 'Only the group admin can send invitations.'})
        

        try:
            invited_user = User.objects.get(username=username, email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found with that username and email.'})

        if group.members.filter(id=invited_user.id).exists():
            return JsonResponse({'success': False, 'message': 'Already a member of this group.'})

        # Check if a pending invitation already exists.
        if GroupRequest.objects.filter(invited_user=invited_user, group=group).exists():
            return JsonResponse({'success': False, 'message': 'An invitation is already pending for this user.'})

        # Create the group invitation.
        group_request = GroupRequest.objects.create(invited_user=invited_user, group=group)

        # Create a notification for the invited user.
        Notification.objects.create(
            user=invited_user,
            sender=request.user,
            type='group_invite',  # Ensure your Notification model includes this type in its choices.
            read=False,
            group_request=group_request,           
        )

        # print(f"group--------------------------->{group_request.group.name}")
        return JsonResponse({'success': True, 'message': f'Invitation sent to {invited_user.username} for {group.name}.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)




logger = logging.getLogger(__name__)

@login_required
@csrf_exempt
def handle_group_request(request):
    """
    Handles a group invitation response.
    Expects JSON with keys: request_id, action (either 'accept' or 'reject').
    """
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            request_id = data.get('request_id')
            action = data.get('action')  # Should be 'accept' or 'reject'

            if not request_id or action not in ['accept', 'reject']:
                return JsonResponse({'success': False, 'message': 'Missing or invalid parameters.'}, status=400)
            
            logger.info("Handling group request: id=%s, action=%s", request_id, action)

            group_request = get_object_or_404(GroupRequest, id=request_id)
            # Ensure that the logged-in user is the invited user.
            if group_request.invited_user != request.user:
                return JsonResponse({'success': False, 'message': 'You are not authorized to respond to this invitation.'})

            
            group = group_request.group
            group_name = group.name

            if action == 'accept':
                # Add the invited user to the group members.
                group.members.add(request.user)
                # Check if a similar notification already exists
                existing_notification = Notification.objects.filter(
                    user=group.admin,
                    sender=request.user,
                    type='group_invite_accepted',
                    group_request=group_request
                ).exists()

                if not existing_notification:
                    # Notify the group admin about acceptance.
                    Notification.objects.create(
                        user=group.admin,
                        sender=request.user,
                        type='group_invite_accepted',
                        read=False,
                        group_request=group_request,
                        extra_data=json.dumps({
                            'group_name': group.name,
                            'group_id': group.id
                        })
                    )
                message = f'You have joined {group.name}.'
            elif action == 'reject':
                # Notify the admin about rejection.
                Notification.objects.create(
                    user=group.admin,
                    sender=request.user,
                    type='group_invite_rejected',
                    read=False,
                    group_request=group_request, 
                    extra_data=json.dumps({
                        'group_name': group.name,
                        'group_id': group.id
                    })          
                )
                message = f'You have rejected the invitation for {group_name}.'
            else:
                return JsonResponse({'success': False, 'message': 'Invalid action.'}, status=400)

            # Delete the group request after a response.
            group_request.delete()

            return JsonResponse({'success': True, 'message': message})
        except Exception as e:
            logger.exception("Error handling group request")
            return JsonResponse({'success': False, 'message': 'Server error: ' + str(e)}, status=500)
        
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)



@login_required
def get_group_profile(request, group_id):
    ist = ZoneInfo("Asia/Kolkata")
    group = get_object_or_404(Group, id=group_id)
    group_profile = group.profile

    is_admin = group.admin == request.user

    # Return the group profile details in JSON response
    return JsonResponse({
        "group_name": group.name,
        "group_avatar": group_profile.group_avatar.url if group_profile.group_avatar else "/group_avatars/group_default.png",
        "group_bio": group_profile.group_bio,
        "group_admin": group_profile.group_admin.username,
        "is_admin": is_admin
    })



@csrf_exempt
@login_required
def update_group_profile(request, group_id):
    ist = ZoneInfo("Asia/Kolkata")
    if request.method == "POST":
        group = get_object_or_404(Group, id=group_id)
        group_profile, created = GroupProfile.objects.get_or_create(group=group)


        # Check if user is the admin
        if request.user != group.admin:
            return JsonResponse({"error": "You are not authorized to edit this group."}, status=403)

        # Get form data
        group_name = request.POST.get("group_name", group.name)
        group_bio = request.POST.get("group_bio", group_profile.group_bio)

        # Update group details
        group.name = group_name
        group_profile.group_bio = group_bio


        # Handle avatar upload
        if "group_avatar" in request.FILES:
            avatar_file = request.FILES["group_avatar"]

            # Delete the old avatar if it exists
            if group_profile.group_avatar:
                try:
                    # Get public_id to delete
                    public_id = group_profile.group_avatar.public_id
                    destroy(public_id)
                except Exception as e:
                    print(f"Warning: Failed to delete old avatar - {e}")

            # Save new avatar
            # avatar_path = f"group_avatars/{group.id}/{avatar_file.name}"
            # saved_path = default_storage.save(avatar_path, ContentFile(avatar_file.read()))
            # group_profile.group_avatar = saved_path  # Update model field

            # ✅ Save new avatar to Cloudinary
            group_profile.group_avatar = avatar_file

        group.save()
        group_profile.save()
        return JsonResponse({"success": True, "message": "Group profile updated successfully!"})

    return JsonResponse({"error": "Invalid request method."}, status=400)







from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse

def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST['email']
        associated_users = User.objects.filter(email=email)

        if associated_users.exists():
            for user in associated_users:
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                reset_link = request.build_absolute_uri(reverse('reset_password_view', kwargs={'uidb64': uid, 'token': token}))

                subject = "Password Reset Request"
                message = render_to_string("reset_email.html", {
                    'user': user,
                    'reset_link': reset_link,
                })

                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            
            messages.success(request, "A password reset link has been sent to your email.")
        else:
            messages.error(request, "No account is associated with this email.")

        return redirect("forgot_password_view")

    return render(request, "forgot_password.html")





from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator

def reset_password_view(request, uidb64, token):
    from django.contrib.auth.models import User

    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            password = request.POST["password"]
            confirm_password = request.POST["confirm_password"]
            if password == confirm_password:
                user.set_password(password)
                user.save()
                messages.success(request, "Password reset successfully! You can now log in.")
                # return redirect("login_view")
            else:
                messages.error(request, "Passwords do not match.")
        return render(request, "reset_password_form.html", {'validlink': True})
    else:
        messages.error(request, "Invalid or expired reset link.")
        return render(request, "reset_password_form.html", {'validlink': False})


def terms_and_conditions(request):
    return render(request, 'terms.html')