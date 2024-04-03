from django.urls import path
from .views import (TweetListCreate, TweetRetrieveDelete, TweetReplies, TweetAncestorsListView, TweetRetweetsList,
     TweetQuotesList, deleteRetweet, likeTweet, unlikeTweet)



urlpatterns = [
   path('', TweetListCreate.as_view()),
   path('retweets/<int:id>/', TweetRetweetsList.as_view(), name='tweet-retweets'),
   path('quotes/<int:id>/', TweetQuotesList.as_view(), name='tweet-quotes'),
   path('like/<int:pk>/', likeTweet, name='like-tweet'),
   path('unlike/<int:pk>/', unlikeTweet, name='unlike-tweet'),
   path('replies/<int:pk>/', TweetReplies.as_view(), name='tweet-replies'),
   path('ancestors/<int:pk>/', TweetAncestorsListView.as_view(), name='tweet-ancestors'),
   path('deleteretweet/<int:pk>/', deleteRetweet, name="deleteretweet"),
   path('<int:pk>/', TweetRetrieveDelete.as_view(), name='tweet-detail'),
]