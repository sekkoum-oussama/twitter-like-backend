from django.db import IntegrityError
from django.db import models
from django.db.models import Subquery, Count, OuterRef, Exists, Case, When
from django.db.models.functions import Coalesce
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListCreateAPIView, RetrieveDestroyAPIView, ListAPIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.contrib.contenttypes.models import ContentType
from notifications.models import Notification
from users.serializers import UserFollowersSerializer
from .serializers import  TweetCreateSerializer, TweetListSerializer
from tweets.throttle import TweetsListCreateThrottle
from .models import  Tweet, Like
from .permissions import IsOwnerOrReadOnly

User = get_user_model()


class TweetListCreate(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TweetCreateSerializer
    throttle_classes = [TweetsListCreateThrottle]

    def get_queryset(self):
        order = self.request.GET.get("order", None)
        id = self.request.GET.get("id", None)
        is_liked = Like.objects.filter(tweet=OuterRef("id"), user=self.request.user).values("id")
        retweeted_is_liked = Like.objects.filter(tweet=OuterRef("related_to"), user=self.request.user).values("id")
        
        queryset = Tweet.objects.annotate(
            is_liked=Case(When(type="retweet", then=Exists(retweeted_is_liked)), default=Exists(is_liked)),
        ).get_tweets(self.request)
        if order is not None and id is not None:
            if order == "newest":
                queryset = list(queryset.filter(id__gt=id).reverse()[0:50])
                queryset.reverse()
            elif order == "oldest":
                queryset = queryset.filter(id__lt=id)
        return queryset[0:50]

    def list(self, request, *args, **kwargs):
        self.serializer_class = TweetListSerializer
        return super().list(request, *args, **kwargs)
        
    def create(self, request, *args, **kwargs):
        data = request.data
        files = request.FILES.getlist('files', None)
        serializer = self.serializer_class(data=data, context = {'files':files})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        show_data_serializer = TweetListSerializer(serializer.instance, context={"request" : request})
        return Response(data=show_data_serializer.data, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class TweetRetrieveDelete(RetrieveDestroyAPIView):
    permission_classes = [IsOwnerOrReadOnly]
    queryset = Tweet.objects.all()
    serializer_class = TweetListSerializer
    
    def get_queryset(self):
        is_liked = Like.objects.filter(tweet=OuterRef("id"), user=self.request.user).values("id")
        retweeted_is_liked = Like.objects.filter(tweet=OuterRef("related_to"), user=self.request.user).values("id")
    
        queryset=Tweet.objects.annotate(
            is_liked=Case(When(type="retweet", then=Exists(retweeted_is_liked)), default=Exists(is_liked)),
        ).get_tweets(self.request) \
        .order_by('date')
        return queryset

class TweetAncestorsListView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TweetListSerializer

    def get_queryset(self):
        tweet_id = self.kwargs['pk']
        tweet = get_object_or_404(Tweet, pk=tweet_id)
        ancestors = self.get_ancestors(tweet)
        return ancestors

    def get_ancestors(self, tweet):
        ancestors = []
        
        quotes_subquery = Tweet.objects.filter(type='quote', related_to=OuterRef("id")).values("type").annotate(nb_quotes=Count("id")).values("nb_quotes")
        retweets_subquery = Tweet.objects.filter(type='retweet', related_to=OuterRef("id")).values("type").annotate(nb_retweets=Count("id")).values("nb_retweets")
        replies_subquery = Tweet.objects.filter(type='reply', related_to=OuterRef("id")).values("type").annotate(nb_replies=Count("id")).values("nb_replies")
        interactions_subquery = Tweet.objects.filter(type__in=["retweet", "quote"], related_to=OuterRef("id")).values("related_to").annotate(nb_interactions=Count("id")).values("nb_interactions")
        is_retweeted_subquery = Tweet.objects.filter(author=self.request.user, type="retweet", related_to=OuterRef("id")).values("id")
        is_liked = Like.objects.filter(tweet=OuterRef("id"), user=self.request.user).values("id")
        
        while tweet.type == "reply":
            #parent_tweet = parent_tweet.related_to
            try:
                tweet = Tweet.objects.filter(pk=tweet.related_to.id).prefetch_related("media") \
                    .select_related("author", "related_to", "related_to__author") \
                    .annotate(
                        retweets=Coalesce(Subquery(retweets_subquery), 0), 
                        quotes=Coalesce(Subquery(quotes_subquery), 0), 
                        replies=Coalesce(Subquery(replies_subquery), 0),
                        likes=Count("tweet_likes"),
                        interactions = Coalesce(Subquery(interactions_subquery), 0),
                        is_retweeted=Exists(is_retweeted_subquery),
                        is_liked=Exists(is_liked),
                    ) \
                    .first()
            except:
                break
            if tweet:
                ancestors.append(tweet)
            else:
                break
            if len(ancestors) >= 10:
                break
        return ancestors


class TweetReplies(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TweetListSerializer

    def get_queryset(self):
        is_liked = Like.objects.filter(tweet=OuterRef("id"), user=self.request.user).values("id")
        retweeted_is_liked = Like.objects.filter(tweet=OuterRef("related_to"), user=self.request.user).values("id")
        quotes_subquery = Tweet.objects.filter(type='quote', related_to=OuterRef("id")).values("type").annotate(nb_quotes=Count("id")).values("nb_quotes")
        retweeted_quotes_subquery = Tweet.objects.filter(type='quote', related_to=OuterRef("related_to")).values("type").annotate(nb_quotes=Count("id")).values("nb_quotes")
        
        retweets_subquery = Tweet.objects.filter(type='retweet', related_to=OuterRef("id")).values("type").annotate(nb_retweets=Count("id")).values("nb_retweets")
        retweeted_retweets_subquery = Tweet.objects.filter(type='retweet', related_to=OuterRef("related_to")).values("type").annotate(nb_retweets=Count("id")).values("nb_retweets")
        
        replies_subquery = Tweet.objects.filter(type='reply', related_to=OuterRef("id")).values("type").annotate(nb_replies=Count("id")).values("nb_replies")
        retweeted_replies_subquery = Tweet.objects.filter(type='reply', related_to=OuterRef("related_to")).values("type").annotate(nb_replies=Count("id")).values("nb_replies")

        interactions_subquery = Tweet.objects.filter(type__in=["retweet", "quote"], related_to=OuterRef("id")).values("related_to").annotate(nb_interactions=Count("id")).values("nb_interactions")
        retweeted_interactions_subquery = Tweet.objects.filter(type__in=["retweet", "quote"], related_to=OuterRef("related_to")).values("related_to").annotate(nb_interactions=Count("id")).values("nb_interactions")
        
        is_retweeted_subquery = Tweet.objects.filter(author=self.request.user, type="retweet", related_to=OuterRef("id")).values("id")
        retweeted_is_retweeted_subquery = Tweet.objects.filter(author=self.request.user, type="retweet", related_to=OuterRef("related_to")).values("id")


        queryset=Tweet.objects.filter(type='reply', related_to=self.kwargs.get('pk')).prefetch_related("media", "tweet_likes", "related_to__media", "related_to__tweet_likes", "related_to__related_to", "related_to__related_to__author", "related_to__related_to__media") \
        .select_related("author", "related_to", "related_to__author") \
        .annotate(
            is_liked=Case(When(type="retweet", then=Exists(retweeted_is_liked)), default=Exists(is_liked)),
            retweets=Coalesce(Case(When(type="retweet", then=Subquery(retweeted_retweets_subquery)), default=Subquery(retweets_subquery)), 0), 
            quotes=Coalesce(Case(When(type="retweet", then=Subquery(retweeted_quotes_subquery)), default=Subquery(quotes_subquery)), 0), 
            replies=Coalesce(Case(When(type="retweet", then=Subquery(retweeted_replies_subquery)), default=Subquery(replies_subquery)), 0),
            likes=Case(When(type="retweet", then=Count("related_to__tweet_likes")), default=Count("tweet_likes")),
            interactions = Coalesce(Case(When(type="retweet", then=Subquery(retweeted_interactions_subquery)), default=Subquery(interactions_subquery)), 0),
            is_retweeted=Case(When(type="retweet", then=Exists(retweeted_is_retweeted_subquery)), default=Exists(is_retweeted_subquery)),
        ) \
        .order_by('-date')
        return queryset
        


class TweetRetweetsList(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserFollowersSerializer

    def get_queryset(self):
        return User.objects.filter(tweets__type="retweet", tweets__related_to=self.kwargs.get("id")) \
            .prefetch_related("tweets") \
            .exclude(id=self.request.user.id) \
            .distinct()[:20]


class TweetQuotesList(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TweetListSerializer

    def get_queryset(self):
        quotes_subquery = Tweet.objects.filter(type='quote', related_to=OuterRef("id")).values("type").annotate(nb_quotes=Count("id")).values("nb_quotes")
        
        retweets_subquery = Tweet.objects.filter(type='retweet', related_to=OuterRef("id")).values("type").annotate(nb_retweets=Count("id")).values("nb_retweets")
        
        replies_subquery = Tweet.objects.filter(type='reply', related_to=OuterRef("id")).values("type").annotate(nb_replies=Count("id")).values("nb_replies")

        interactions_subquery = Tweet.objects.filter(type__in=["retweet", "quote"], related_to=OuterRef("id")).values("related_to").annotate(nb_interactions=Count("id")).values("nb_interactions")
        
        is_retweeted_subquery = Tweet.objects.filter(author=self.request.user, type="retweet", related_to=OuterRef("id")).values("id")

        is_liked = Like.objects.filter(tweet=OuterRef("id"), user=self.request.user).values("id")
        
        queryset=Tweet.objects.filter(type="quote", related_to=self.kwargs.get("id")) \
        .prefetch_related("media", "tweet_likes", "related_to__media",) \
        .select_related("author", "related_to", "related_to__author") \
        .annotate(
            retweets=Coalesce(Subquery(retweets_subquery), 0), 
            quotes=Coalesce(Subquery(quotes_subquery), 0), 
            replies=Coalesce(Subquery(replies_subquery), 0),
            likes=Count("tweet_likes"),
            interactions = Coalesce(Subquery(interactions_subquery), 0),
            is_retweeted=Exists(is_retweeted_subquery),
            is_liked=Exists(is_liked),
        ) \
        .order_by('-date')
        return queryset


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def deleteRetweet(request, pk):
    try:
        deleted_objs_count, _ = Tweet.objects.filter(type="retweet", related_to=pk, author=request.user).delete()
        if deleted_objs_count > 0:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)
    except Exception as error:
        return Response(data=str(error), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def likeTweet(request, pk):
    tweet = get_object_or_404(Tweet, pk=pk)
    Like.objects.create(user=request.user, tweet=tweet)
    try:
        Notification.objects.create(profile=request.user, type='like', content=tweet)
    except IntegrityError:
        pass
    return Response(data=pk, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unlikeTweet(request, pk):
    tweet = get_object_or_404(Tweet, pk=pk)
    Like.objects.filter(user=request.user, tweet=tweet).delete()
    tweet_content_type = ContentType.objects.get(app_label='tweets', model='tweet')
    Notification.objects.filter(profile=request.user, type='like', content_type=tweet_content_type, object_id=tweet.id).delete()
    return Response(data=pk, status=status.HTTP_204_NO_CONTENT)