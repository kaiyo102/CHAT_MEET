from django.db import models

from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserChatManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username field must be set')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class UserChat(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=200)
    profile_picture = models.ImageField(upload_to='profile_pictures/')
    full_name = models.CharField(max_length=200, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    warning_count = models.IntegerField(default=0)
    day_start = models.DateField(blank=True, null=True)
    day_end = models.DateField(blank=True, null=True)
    block_count = models.IntegerField(default=0)
    block_forever = models.BooleanField(default=False)

    # Các trường Django quản lý người dùng
    is_staff = models.BooleanField(default=False)  # Cần cho quyền truy cập vào admin
    is_superuser = models.BooleanField(default=False)  # Cần cho quyền admin

    objects = UserChatManager()

    USERNAME_FIELD = 'username'  # Trường xác thực
    REQUIRED_FIELDS = ['email']  # Các trường yêu cầu khi tạo user

    def get_full_name(self):
        return self.full_name or self.username

    def get_short_name(self):
        return self.username

    def __str__(self):
        return self.username
    
class FriendRequest(models.Model):
    sender = models.ForeignKey(UserChat, on_delete=models.CASCADE, related_name='sent_friend_requests')
    receiver = models.ForeignKey(UserChat, on_delete=models.CASCADE, related_name='received_friend_requests')
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected'), ('canceled', 'Canceled'), ('recalled', 'Recalled')],
        default='pending'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} → {self.receiver.username} - {self.status}"

    # Đảm bảo rằng không thể có nhiều hơn một yêu cầu kết bạn giữa hai người dùng
    def clean(self):
        if FriendRequest.objects.filter(sender=self.sender, receiver=self.receiver).exclude(id=self.id).exists():
            raise ValidationError("A friend request already exists between these two users.")

class Friends(models.Model):
    user = models.ForeignKey(UserChat, on_delete=models.CASCADE, related_name='user_friends')
    friend = models.ForeignKey(UserChat, on_delete=models.CASCADE, related_name='friend')

class ChatRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    users = models.ManyToManyField(UserChat, related_name='chat_rooms')

    def __str__(self):
        return self.name

class Message(models.Model):
    room_name = models.ForeignKey(ChatRoom, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(UserChat, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(UserChat, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    image = models.ImageField(upload_to="chat_images/", blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to="chat_files/", blank=True, null=True)  # Thêm trường này

    class Meta:
        ordering = ('date_added',)

class MeetingRoom(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Tên phòng họp
    host = models.ForeignKey(UserChat, on_delete=models.CASCADE, related_name='hosted_meeting_rooms')  # Một người tổ chức
    participants = models.ManyToManyField(UserChat, related_name='joined_meeting_rooms', blank=True)  # Nhiều người tham gia

    def __str__(self):
        return self.name