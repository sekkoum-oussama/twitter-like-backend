from email.policy import default
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from moviepy.editor import VideoFileClip
import os
from django.core.files import File
from .custom_queries import CustomTweetQuery

User = get_user_model()


def validate_media_type(value):
    extension = value.split('.')[-1]
    if extension in ['jpg', 'jpeg', 'mp4']:
        return value
    else:
        raise ValidationError('Only pictures and videos are accepted')

def validate_tweet_type(value):
    if value not in ['reply', 'quote', 'retweet', None]:
        raise ValidationError("Tweet type should be either 'null', 'reply', 'quote' or 'retweet'")
    else:
        return value


class Tweet(models.Model):
    author = models.ForeignKey(User, related_name='tweets', on_delete=models.CASCADE)
    text = models.CharField(max_length=250, null=True, default=None)
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50, default=None, null=True, blank=True, validators=[validate_tweet_type])
    related_to = models.ForeignKey('self', on_delete=models.CASCADE, default=None, blank=True, null=True)

    objects = CustomTweetQuery.as_manager()

    def __str__(self) -> str:
        return str(self.pk)
        #return "{} on : {}".format(self.author.email, self.date)
        

class Media(models.Model):
    tweet = models.ForeignKey('Tweet', related_name='media', on_delete=models.CASCADE)
    file = models.FileField(validators=[validate_media_type])
    thumbnail = models.ImageField(upload_to='videos_thumbnails', null=True, blank=True, default='default_thumbnail/default_thumbnail.jpg')

    def generate_thumbnail(self):
        if self.file.name.endswith('.mp4'):
            video_path = self.file.path
            thumbnail_path = self.file.path.replace('.mp4', '.jpg')

            try:
                clip = VideoFileClip(video_path)
                clip.save_frame(thumbnail_path, t=0)

                # Save the generated thumbnail to the media file
                thumbnail_name = self.file.name.replace(".mp4", ".jpg")
                self.thumbnail.save(thumbnail_name, File(open(thumbnail_path, 'rb')))

                # Clean up the temporary frame
                os.remove(thumbnail_path)

            except Exception as e:
                pass


class Like(models.Model):
    user = models.ForeignKey(User, related_name='user_like', on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, related_name='tweet_likes', on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)

