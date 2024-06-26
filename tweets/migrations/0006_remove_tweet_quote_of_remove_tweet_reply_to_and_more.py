# Generated by Django 4.0.3 on 2022-04-25 18:34

from django.db import migrations, models
import django.db.models.deletion
import tweets.models


class Migration(migrations.Migration):

    dependencies = [
        ('tweets', '0005_like'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tweet',
            name='quote_of',
        ),
        migrations.RemoveField(
            model_name='tweet',
            name='reply_to',
        ),
        migrations.RemoveField(
            model_name='tweet',
            name='retweet_of',
        ),
        migrations.AddField(
            model_name='tweet',
            name='related_to',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='tweets.tweet'),
        ),
        migrations.AddField(
            model_name='tweet',
            name='type',
            field=models.CharField(default=None, max_length=50, validators=[tweets.models.validate_tweet_type]),
        ),
    ]
