# Generated by Django 4.0.3 on 2022-09-23 00:23

from django.db import migrations
import tweets.custom_fields


class Migration(migrations.Migration):

    dependencies = [
        ('tweets', '0023_tweet_likes_alter_like_tweet_alter_like_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tweet',
            name='date',
            field=tweets.custom_fields.CustomDateTimeModelField(auto_now_add=True),
        ),
    ]
