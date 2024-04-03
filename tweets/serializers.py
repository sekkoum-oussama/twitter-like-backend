from django.contrib.auth import get_user_model
from rest_framework.serializers import ModelSerializer, ValidationError, HyperlinkedModelSerializer, HyperlinkedIdentityField
from rest_framework import serializers
from rest_framework.reverse import reverse
from tweets.models import Like, Tweet, Media

User = get_user_model()

class AuthorTweetDetailsSerializer(HyperlinkedModelSerializer):
    url = HyperlinkedIdentityField(view_name='profile-detail', lookup_field='username')
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'avatar')


class MediaSerializer(ModelSerializer):
    class Meta:
        model = Media
        fields = ('file',"thumbnail")


class TweetCreateSerializer(ModelSerializer):
    text = serializers.CharField(default=None)
    type = serializers.CharField(default=None)
    related_to = serializers.PrimaryKeyRelatedField(queryset=Tweet.objects.all(), default=None)

    class Meta:
        model = Tweet
        fields = ('id', 'text', 'type', 'related_to')

    def validate(self, attrs):
        files = self.context['files']
        if attrs['text'] is None and (files is None or len(files) < 1) and attrs['type'] != 'retweet':
            raise ValidationError({'empty tweet' : 'A tweet should contain a text, photo or video'})
        if attrs['type'] is None and attrs['related_to'] is not None:
            raise ValidationError({'tweet related to error' : 'A normal tweet should not be related to any tweet'})
        if attrs['type'] is not None and attrs['related_to'] is None:
            raise ValidationError({'bad related to' : 'This type of tweets should be related to another tweet'})
        if files is not None:
            if len(files) > 4:
                raise ValidationError({ 'Too many files' : 'Only 4 files can be posted'})
            '''if len(files) > 1 and attrs['type'] == 'reply':
                raise ValidationError({'reply with files' : 'A reply can have only one file'})
            
            if len(files) > 1 and attrs['type'] == 'quote':
                raise ValidationError({'quote with files' : 'A quote can have only one file'})
            '''
            for file in files:
                    extension = file.name.split('.')[-1]
                    if extension not in ['jpg', 'jpeg', 'mp4']:
                        raise ValidationError({'Forbidden types uploaded' : 'Only pictures and videos can be posted as files'})
            '''        if extension == 'jpg' or 'jpeg':
                        types.add('photo')
                    elif extension == 'mp4':
                        types.add('video')
                    if len(types) > 1:
                        raise ValidationError({'multiple types uploaded' : 'You can attach only photos or only videos, not the two at the same time'})
            '''
        return super().validate(attrs)

    def create(self, validated_data):
        files = self.context['files']
        tweet = Tweet.objects.create(**validated_data)
        for file in files:
            media = Media(tweet=tweet, file=file)
            media.save()
            media.generate_thumbnail()
        return tweet


class QuotedTweetSerializer(HyperlinkedModelSerializer):
    author = AuthorTweetDetailsSerializer()
    media = MediaSerializer(many=True)
    class Meta:
        model = Tweet
        fields = ('id', 'url', 'author', 'text', 'date', 'media')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if instance.type == 'reply':
            ret['reply_to'] = instance.author.username
        return ret


class TweetListSerializer(ModelSerializer):
    retweets = serializers.IntegerField(default=0)
    quotes = serializers.IntegerField(default=0)
    replies = serializers.IntegerField(default=0)
    is_retweeted = serializers.BooleanField(default=False)
    is_liked = serializers.BooleanField(default=False)
    media = MediaSerializer(many=True)
    likes = serializers.IntegerField(default=0)
    interactions = serializers.IntegerField(default=0)
    
    class Meta:
        model = Tweet
        fields = ('id', 'type', 'retweets', 'quotes', 'replies', 'is_retweeted', 'is_liked', 'likes', 'interactions','media')
    
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        req = self.context.get('request')
        if instance.type == None:
            ret['url'] = reverse('tweet-detail', args=[instance.id], request=req)
            ret['author'] = AuthorTweetDetailsSerializer(context={'request':req}, instance=instance.author).data
            ret['text'] = instance.text
            ret['date'] = instance.date.replace(tzinfo=None).isoformat(' ')
        if instance.type == 'reply':
            ret['url'] = reverse('tweet-detail', args=[instance.id], request=req)
            ret['author'] = AuthorTweetDetailsSerializer(context={'request':req}, instance=instance.author).data
            ret['text'] = instance.text
            ret['date'] = instance.date.replace(tzinfo=None).isoformat(' ')
            ret['reply_to'] = instance.related_to.author.username
        if instance.type == 'quote':
            ret['url'] = reverse('tweet-detail', args=[instance.id], request=req)
            ret['author'] = AuthorTweetDetailsSerializer(context={'request':req}, instance=instance.author).data
            ret['text'] = instance.text
            ret['date'] = instance.date.replace(tzinfo=None).isoformat(' ')
            ret['quoted_tweet'] = QuotedTweetSerializer(context={'request':req}, instance=instance.related_to).data
        if instance.type == 'retweet':
            ret['author'] = instance.author.username
            ret['url'] = reverse('tweet-detail', args=[instance.id], request=req)
            ret['related_to'] = {
                'id' : instance.related_to.id,
                'url' : reverse('tweet-detail', args=[instance.related_to.id], request=req),
                'type' : instance.related_to.type,
                'author' : AuthorTweetDetailsSerializer(context={'request':req}, instance=instance.related_to.author).data,
                'text' : instance.related_to.text,
                'date' : instance.related_to.date.replace(tzinfo=None).isoformat(' '),
                'media' : MediaSerializer(many=True, instance=instance.related_to.media, context={'request':req}).data,
                'replies' : ret["replies"], #Tweet.objects.filter(type='reply', related_to=instance.related_to).count(),
                'interactions' : ret["interactions"], #Tweet.objects.filter(type__in=['retweet','quote'], related_to=instance.related_to).count(),
                'likes' : ret["likes"], #Like.objects.filter(tweet=instance.related_to).count(),
                'is_liked' : ret["is_liked"], #Like.objects.filter(tweet=instance.related_to, user=req.user).exists(),
                'is_retweeted' : ret["is_retweeted"], #Tweet.objects.filter(author=req.user, type="retweet", related_to=instance.related_to).exists(),
                'retweets' : ret["retweets"], #Tweet.objects.filter(type='retweet', related_to=instance.related_to).count(),
                'quotes' : ret["quotes"], #Tweet.objects.filter(type='quote', related_to=instance.related_to).count(),
            }
            if instance.related_to.type == 'reply':
                ret['related_to']['reply_to'] = instance.related_to.related_to.author.username
            elif instance.related_to.type =='quote':
                ret['related_to']['quoted_tweet'] = QuotedTweetSerializer(context={'request':req}, instance=instance.related_to.related_to).data
        return ret
