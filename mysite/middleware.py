from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from accounts.models import Profile

class ActiveUserMiddleware(MiddlewareMixin):

    def process_request(self, request):
        # print(request.user)
        if request.user.is_authenticated:
            cache.set('seen_%s' %(request.user.username), timezone.now(), settings.USER_LASTSEEN_TIMEOUT)
            update_last_seen = Profile.objects.get(user=request.user)
            update_last_seen.last_seen = timezone.now()
            update_last_seen.save()
