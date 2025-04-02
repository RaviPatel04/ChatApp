from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils.timezone import now
import threading
import time


# Create your models here.
class ContactUs(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=10, blank=True, null=True)
    communication_method = models.CharField(max_length=10, choices=[('email', 'Email'), ('phone', 'Phone')], default='email')  # Added communication method
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name}"
    


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    
    def clean(self):
        # Add email validation at the model level
        if self.user.email and User.objects.filter(email=self.user.email).exclude(id=self.user.id).exists():
            raise ValidationError({'email': 'This email is already in use.'})
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


    

class Friendship(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friends")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="friends_of")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')  # Ensure a unique friendship
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user1.username} <-> {self.user2.username}"




class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    text = models.TextField()
    audio = models.FileField(upload_to="voice_messages/", blank=True, null=True)
    file = models.FileField(upload_to="chat_files/",blank=True, null=True)
    timestamp = models.DateTimeField(default=now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        if self.text:
            return f"{self.sender.username} -> {self.receiver.username}: {self.text[:30]}"
        else:
            return f"{self.sender.username} -> {self.receiver.username}: [File Sent]"



#26/02/25
class FriendRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete_after_20_seconds(self):
        """ Automatically delete the friend request after 20 seconds if accepted or rejected """
        def delete_request():
            time.sleep(20)  # Wait 20 seconds
            self.delete()    # Delete the FriendRequest

        if self.status in ["accepted", "rejected"]:
            threading.Thread(target=delete_request).start()

    def save(self, *args, **kwargs):
        """ Override save to trigger deletion on status change """
        super().save(*args, **kwargs)  # Save first
        if self.status in ["accepted", "rejected"]:
            self.delete_after_20_seconds()  # Start deletion timer

    
    class Meta:
        unique_together = ('sender', 'receiver')
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"
    
















#27/03/2025
class Group(models.Model):
    name = models.CharField(max_length=100)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_groups")
    members = models.ManyToManyField(User, related_name='custom_groups',blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

    
    
class GroupMessage(models.Model):
    group = models.ForeignKey(Group,on_delete=models.CASCADE,related_name="messages")
    sender = models.ForeignKey(User,on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    audio = models.FileField(upload_to="voice_messages/", blank=True, null=True)
    file = models.FileField(upload_to="chat_files/",blank=True,null=True)
    timestamp = models.DateTimeField(default=now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Group: {self.group.name} | Sender: {self.sender.username}"

# 27/03/2025
class GroupRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    # The user being invited (user2)
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_group_requests')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')


    def __str__(self):
        return f"{self.group.admin.username} invites {self.invited_user.username} to {self.group.name} ({self.status})"

        # admin_username = self.group.admin.username if self.group and self.group.admin else 'Unknown Admin'
        # invited_username = self.invited_user.username if self.invited_user else 'Unknown User'
        # return f"{admin_username} invites {invited_username} to {self.group.name} ({self.status})"
















class Notification(models.Model):
    TYPE_CHOICES = (
        ('friend_request', 'Friend Request'),
        ('request_accepted', 'Request Accepted'),
        ('request_rejected', 'Request Rejected'),
        ('group_invite', 'Group Invite'),
        ('group_invite_accepted', 'Group Invite Accepted'),
        ('group_invite_rejected', 'Group Invite Rejected'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    type = models.CharField(max_length=40, choices=TYPE_CHOICES)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_request = models.ForeignKey(FriendRequest, on_delete=models.SET_NULL, null=True, blank=True)
    group_request = models.ForeignKey(GroupRequest, on_delete=models.SET_NULL, null=True, blank=True)
    extra_data = models.TextField(null=True, blank=True)

    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.type} from {self.sender.username} to {self.user.username}"

# Signal to create notification when friend request is created
@receiver(post_save, sender=FriendRequest)
def create_notification(sender, instance, created, **kwargs):
    if created:
        # New friend request - notify receiver
        Notification.objects.create(
            user=instance.receiver,
            sender=instance.sender,
            type='friend_request',
            related_request=instance
        )
    elif instance.status == 'accepted':
        # Friend request accepted - notify sender
        Notification.objects.create(
            user=instance.sender,
            sender=instance.receiver,
            type='request_accepted',
            related_request=instance
        )
    elif instance.status == 'rejected':
        # Friend request rejected - notify sender
        Notification.objects.create(
            user=instance.sender,
            sender=instance.receiver,
            type='request_rejected',
            related_request=instance
        )

# Signal to create friendship when friend request is accepted
@receiver(post_save, sender=FriendRequest)
def create_friendship(sender, instance, **kwargs):
    if instance.status == 'accepted':
        # Create friendship connection
        Friendship.objects.get_or_create(
            user1=instance.sender,
            user2=instance.receiver
        )





    

# class GroupRequest(models.Model):
#     STATUS_CHOICES = (
#         ('pending', 'Pending'),
#         ('accepted', 'Accepted'),
#         ('rejected', 'Rejected'),
#     )
#     # The invited user who will decide whether to join the group.
#     sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_group_requests')
#     group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_requests')
#     status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.sender.username} -> {self.group.name} ({self.status})"    

from django.db.models.signals import post_save
from django.dispatch import receiver

class GroupProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='profile')
    group_avatar = models.ImageField(upload_to='group_avatars/', default='group_avatars/group_default.png')
    group_bio = models.TextField(max_length=500, blank=True)
    group_admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_admins')
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Profile of {self.group.name}"


@receiver(post_save, sender=Group)
def create_group_profile(sender, instance, created, **kwargs):
    if created:
        GroupProfile.objects.create(group=instance, group_admin=instance.admin)

@receiver(post_save, sender=Group)
def save_group_profile(sender, instance, **kwargs):
    instance.profile.save()
