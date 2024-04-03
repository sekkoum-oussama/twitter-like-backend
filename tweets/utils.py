from django.contrib.auth import get_user_model
from tweets.models import Tweet


User = get_user_model()

def getAuthorsOfReplies(tweet):
    authors = list()
    current_tweet = tweet
    nb_of_queries = 5
    while current_tweet.type == 'reply' and nb_of_queries > 0:
        authors.insert(0, current_tweet.related_to.author.username)
        current_tweet = current_tweet.related_to
        nb_of_queries -= 1
    return list(dict.fromkeys(authors))
