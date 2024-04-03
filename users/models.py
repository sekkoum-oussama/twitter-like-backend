from users.users_manager import ProfileManager
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin


class Profile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, blank=False, null=False)
    username = models.CharField(max_length=100, blank=False, null=False, unique=True, db_index=True)
    date_birth = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='users_avatars',default='default_avatar/default_avatar.png')
    cover = models.ImageField(upload_to='users_covers',default='default_cover/default_cover.png')
    bio = models.TextField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    date_joined = models.DateField(auto_now_add=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    following = models.ManyToManyField('self', related_name='followers', through='Followers', symmetrical=False,)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = ProfileManager()

    def __str__(self) -> str:
        return self.username
    

class Followers(models.Model):
    user_from = models.ForeignKey(Profile, related_name='from_user', on_delete=models.CASCADE,)
    user_to = models.ForeignKey(Profile, related_name=('to_user'), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)