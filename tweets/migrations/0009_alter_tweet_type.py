# Generated by Django 4.0.3 on 2022-06-06 23:44

from django.db import migrations, models
import tweets.models


class Migration(migrations.Migration):

    dependencies = [
        ('tweets', '0008_alter_media_file_alter_media_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tweet',
            name='type',
            field=models.CharField(blank=True, default=None, max_length=50, null=True, validators=[tweets.models.validate_tweet_type]),
        ),
    ]
