
from django.db.models import QuerySet, OuterRef, Count, Subquery, Exists, Case, When
from django.db.models.functions import Coalesce


class CustomTweetQuery(QuerySet):
    def get_tweets(self, request):
        quotes_subquery = self.filter(type='quote', related_to=OuterRef("id")).values("type").annotate(nb_quotes=Count("id")).values("nb_quotes")
        retweeted_quotes_subquery = self.filter(type='quote', related_to=OuterRef("related_to")).values("type").annotate(nb_quotes=Count("id")).values("nb_quotes")
        
        retweets_subquery = self.filter(type='retweet', related_to=OuterRef("id")).values("type").annotate(nb_retweets=Count("id")).values("nb_retweets")
        retweeted_retweets_subquery = self.filter(type='retweet', related_to=OuterRef("related_to")).values("type").annotate(nb_retweets=Count("id")).values("nb_retweets")
        
        replies_subquery = self.filter(type='reply', related_to=OuterRef("id")).values("type").annotate(nb_replies=Count("id")).values("nb_replies")
        retweeted_replies_subquery = self.filter(type='reply', related_to=OuterRef("related_to")).values("type").annotate(nb_replies=Count("id")).values("nb_replies")

        interactions_subquery = self.filter(type__in=["retweet", "quote"], related_to=OuterRef("id")).values("related_to").annotate(nb_interactions=Count("id")).values("nb_interactions")
        retweeted_interactions_subquery = self.filter(type__in=["retweet", "quote"], related_to=OuterRef("related_to")).values("related_to").annotate(nb_interactions=Count("id")).values("nb_interactions")
        
        is_retweeted_subquery = self.filter(author=request.user, type="retweet", related_to=OuterRef("id")).values("id")
        retweeted_is_retweeted_subquery = self.filter(author=request.user, type="retweet", related_to=OuterRef("related_to")).values("id")


        queryset=self.prefetch_related("media", "tweet_likes", "related_to__media", "related_to__tweet_likes", "related_to__related_to", "related_to__related_to__author", "related_to__related_to__media") \
        .select_related("author", "related_to", "related_to__author") \
        .annotate(
            retweets=Coalesce(Case(When(type="retweet", then=Subquery(retweeted_retweets_subquery)), default=Subquery(retweets_subquery)), 0), 
            quotes=Coalesce(Case(When(type="retweet", then=Subquery(retweeted_quotes_subquery)), default=Subquery(quotes_subquery)), 0), 
            replies=Coalesce(Case(When(type="retweet", then=Subquery(retweeted_replies_subquery)), default=Subquery(replies_subquery)), 0),
            likes=Case(When(type="retweet", then=Count("related_to__tweet_likes")), default=Count("tweet_likes")),
            interactions = Coalesce(Case(When(type="retweet", then=Subquery(retweeted_interactions_subquery)), default=Subquery(interactions_subquery)), 0),
            is_retweeted=Case(When(type="retweet", then=Exists(retweeted_is_retweeted_subquery)), default=Exists(is_retweeted_subquery)),
        ) \
        .order_by('-date')
        return queryset