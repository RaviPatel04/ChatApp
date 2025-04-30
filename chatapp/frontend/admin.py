from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django import forms
from .models import Profile, ContactUs, FriendRequest, Friendship, Message,  Notification, Group, GroupMessage, GroupRequest, GroupProfile


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'is_active', 'is_staff', 'is_superuser')


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('avatar', 'bio', 'phone')


class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    list_display = ('username', 'email', 'get_phone', 'get_communication_method', 'is_active')
    search_fields = ('username', 'email', 'profile__phone')
    list_filter = ('is_active',)
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    inlines = [ProfileInline]

    def get_phone(self, obj):
        return obj.profile.phone if hasattr(obj, 'profile') else 'N/A'
    get_phone.short_description = 'Phone'

    def get_communication_method(self, obj):
        return obj.profile.communication_method if hasattr(obj.profile, 'communication_method') else 'N/A'
    get_communication_method.short_description = 'Communication Method'

    def save_model(self, request, obj, form, change):
        if change and 'email' in form.changed_data:
            # Validate email uniqueness
            if User.objects.filter(email=obj.email).exclude(id=obj.id).exists():
                from django.core.exceptions import ValidationError
                raise ValidationError('This email is already in use.')
        super().save_model(request, obj, form, change)


# Unregister default User model and register the customized one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# Register ContactUs Model
@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'communication_method', 'message', 'created_at')  
    search_fields = ('name', 'email', 'message')  
    list_filter = ('created_at',)

# Register Profile separately for direct access in the admin panel
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__username', 'phone')



class ConversationFilter(admin.SimpleListFilter):
    """Custom filter to show messages between selected users"""
    title = "Conversation With"
    parameter_name = "conversation_user"

    def lookups(self, request, model_admin):
        # Get all unique users in messages
        unique_users = set(
            list(Message.objects.values_list("sender__username", flat=True)) +
            list(Message.objects.values_list("receiver__username", flat=True))
        )
        return [(user, user) for user in unique_users if user != request.user.username]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(sender__username=self.value()) | queryset.filter(receiver__username=self.value())
        return queryset



@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("formatted_sender", "formatted_receiver", "short_text", "timestamp", "is_read")
    search_fields = ("sender__username", "receiver__username", "text")
    list_filter = (ConversationFilter, "is_read", "timestamp")  
    ordering = ("-timestamp",) 

    def formatted_sender(self, obj):
        return f"📤 {obj.sender.username}"
    formatted_sender.short_description = "Sender"

    def formatted_receiver(self, obj):
        return f"📥 {obj.receiver.username}"
    formatted_receiver.short_description = "Receiver"

    def short_text(self, obj):
        return obj.text[:30] + ("..." if len(obj.text) > 30 else "")
    short_text.short_description = "Message"



@admin.register(FriendRequest)
class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('sender__username', 'receiver__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('user1', 'user2', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user1__username', 'user2__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'sender', 'type', 'read', 'created_at')
    list_filter = ('type', 'read', 'created_at')
    search_fields = ('user__username', 'sender__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)
    raw_id_fields = ('user', 'sender', 'related_request')



@admin.register(GroupProfile)
class GroupProfileAdmin(admin.ModelAdmin):
    list_display = ('group', 'group_admin', 'created_at')
    search_fields = ('group__name', 'group_admin__username') 

class GroupProfileInline(admin.StackedInline):
    model = GroupProfile
    can_delete = False
    verbose_name_plural = 'Group Profile'
    fields = ('group_avatar', 'group_bio', 'group_admin')


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name','admin','created_at')
    search_fields = ('name','admin__username')
    filter_horizontal = ('members',)
    inlines = [GroupProfileInline]

@admin.register(GroupMessage)
class GroupMessageAdmin(admin.ModelAdmin):
    list_display = ('group','sender','short_text','timestamp')
    search_fields = ('group__name', 'sender__username', 'text')
    ordering = ('-timestamp',)

    def short_text(self,obj):
        return (obj.text[:30] + '...') if len(obj.text) > 30 else obj.text
    
    short_text.short_description = "Message Preview"


@admin.register(GroupRequest)
class GroupRequestAdmin(admin.ModelAdmin):
    list_display = ('invited_user', 'group', 'created_at')
    list_filter = ('group', 'created_at')
    search_fields = ('invited_user__username', 'group__name')
    