from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin


urlpatterns = [
    path("", views.home, name="home"),
    path("contact/", views.contact, name="contact"),
    path("register/", views.register_view, name="register_view"),
    path("login/", views.login_view, name="login_view"),
    path("logout/", views.logout_view, name="logout_view"),
    path("about/", views.about, name="about"),
    path("chat/", views.chat, name="chat"),
    path("update_profile/", views.update_profile, name="update_profile"),

    path("get-messages/<int:friend_id>/", views.get_messages, name="get_messages"),  
    path("send-message/", views.send_message, name="send_message"),
    path("send-voice-message/", views.send_voice_message, name="send_voice_message"),
    path("get-user-profile/<int:user_id>/", views.get_user_profile, name="get-user-profile"),

    path("send-attachment/", views.send_attachment, name="send_attachment"),


    path('send-friend-request/', views.send_friend_request, name='send_friend_request'),
    path('handle-friend-request/', views.handle_friend_request, name='handle_friend_request'),
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/mark-read/', views.mark_notification_read, name='mark_notification_read'),
    path('friends/', views.get_friends, name='get_friends'),
    path('notifications/count/', views.get_notification_count, name='get_notification_count'),
    path('notifications/<int:notification_id>/delete/', views.delete_notification, name='delete_notification'),


    # 27/03/2025
    path('create-group/', views.create_group, name='create_group'),
    path('get-group-messages/<int:group_id>/', views.get_group_messages, name='get_group_messages'),
    path('send-group-message/', views.send_group_message, name='send_group_message'),
    # path('invite-to-group/', views.invite_to_group, name='invite_to_group'),
    path('send-group-invite/', views.send_group_invite, name='send_group_invite'),
    path('handle-group-request/', views.handle_group_request, name='handle_group_request'),
    path('get-group-profile/<int:group_id>/', views.get_group_profile, name="get-group-profile"),
    path("update-group-profile/<int:group_id>/", views.update_group_profile, name="update-group-profile"),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)