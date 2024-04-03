from django.db import IntegrityError
from django.db.models import Count, OuterRef, When, Exists, Subquery, Case
from django.db.models.functions import Coalesce
from django.db.models.query import prefetch_related_objects
from django.shortcuts import get_object_or_404
from dj_rest_auth.views import UserDetailsView
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification
from tweets.serializers import TweetListSerializer
from tweets.models import Tweet, Like
from users.permissions import IsSameUserOrReadOnly
from users.serializers import UserDetailSerializer, UserFollowersSerializer


User = get_user_model()

class UserDetailView(RetrieveUpdateAPIView):
    permission_classes = [IsSameUserOrReadOnly]
    serializer_class = UserDetailSerializer
    queryset = User.objects.all()
    lookup_field = 'username'

    def get_queryset(self):
        return User.objects.filter(username=self.kwargs.get('username')) \
            .prefetch_related("followers") \
            .annotate(
                user_followers = Count("followers"),
                user_following = Count("following")
            )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["files"] = self.request.FILES
        context["request"] = self.request
        return context

class UserTweetsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TweetListSerializer
    username = None
    def list(self, request, *args, **kwargs):
        self.username = self.kwargs.get('username')
        get_object_or_404(User, username=self.username)
        return super().list(self, request, *args, **kwargs)
        
    def get_queryset(self):
        is_liked = Like.objects.filter(tweet=OuterRef("id"), user=self.request.user).values("id")
        retweeted_is_liked = Like.objects.filter(tweet=OuterRef("related_to"), user=self.request.user).values("id")
        
        queryset = Tweet.objects.annotate(
            is_liked=Case(When(type="retweet", then=Exists(retweeted_is_liked)), default=Exists(is_liked)),
        ).get_tweets(self.request)
        if self.username != None:
            queryset = queryset.filter(author__username__iexact=self.username)
        return queryset


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def userFollow(request, username):
    other_user = get_object_or_404(User, username=username)
    request.user.following.add(other_user)
    try:
        Notification.objects.create(profile=request.user, type='follow', content=other_user)
    except IntegrityError:
        pass
    return Response(status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def userUnfollow(request, username):
    other_user = get_object_or_404(User, username=username)
    request.user.following.remove(other_user)
    users_content_type = ContentType.objects.get(app_label='users', model='profile')
    Notification.objects.filter(profile=request.user, type='follow', content_type=users_content_type, object_id=other_user.id).delete()
    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getFollowers(request, username=None):
    user = get_object_or_404(User, username=username)
    user_followers = user.followers.exclude(id=request.user.id)
    prefetch_related_objects(user_followers, "followers")
    serializer = UserFollowersSerializer(many=True, instance=user_followers, context={'request':request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getFollowing(request, username=None):
    user = get_object_or_404(User, username=username)
    user_followers = user.following.exclude(id=request.user.id)
    prefetch_related_objects(user_followers, "followers")
    serializer = UserFollowersSerializer(many=True, instance=user_followers, context={'request':request})
    return Response(serializer.data)