# Generated by Django 4.0.3 on 2023-11-04 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tweets', '0026_remove_tweet_likes_alter_like_tweet'),
    ]

    operations = [
        migrations.AddField(
            model_name='media',
            name='thumbnail',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='videos_thumbnails/'),
        ),
    ]