# Generated by Django 4.0.3 on 2022-06-22 23:07

from django.db import migrations, models
import tweets.models


class Migration(migrations.Migration):

    dependencies = [
        ('tweets', '0013_alter_tweet_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tweet',
            name='type',
            field=models.CharField(default=None, max_length=50, null=True, validators=[tweets.models.validate_tweet_type]),
        ),
    ]
