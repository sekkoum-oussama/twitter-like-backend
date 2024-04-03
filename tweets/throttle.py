from rest_framework.throttling import UserRateThrottle

class TweetsListCreateThrottle(UserRateThrottle):
    rate = '10/minute'
