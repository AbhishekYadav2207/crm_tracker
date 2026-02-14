
import time
from django.conf import settings
from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin

class SessionTimeoutMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        current_time = time.time()
        last_activity = request.session.get('last_activity')

        if last_activity:
            # If SESSION_COOKIE_AGE is set, use it; otherwise default to 30 mins
            timeout_duration = getattr(settings, 'SESSION_COOKIE_AGE', 1800)
            
            if current_time - last_activity > timeout_duration:
                logout(request)
                request.session.flush()
                return
        
        request.session['last_activity'] = current_time
