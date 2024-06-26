# Generated by Django 4.0.3 on 2022-04-21 21:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tweets', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tweet',
            name='quote_of',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quotes', to='tweets.tweet'),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='reply_to',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='tweets.tweet'),
        ),
        migrations.AlterField(
            model_name='tweet',
            name='retweet_of',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='retweets', to='tweets.tweet'),
        ),
    ]
