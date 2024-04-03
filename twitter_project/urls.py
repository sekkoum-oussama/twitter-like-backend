from urllib import response
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static 
from dj_rest_auth.views import PasswordResetView, PasswordResetConfirmView
from dj_rest_auth.jwt_auth import get_refresh_view
from rest_framework_simplejwt.views import TokenVerifyView
from dj_rest_auth.registration.views import ResendEmailVerificationView, VerifyEmailView
from rest_framework.schemas import get_schema_view
from django.views.generic import TemplateView



urlpatterns = [
    path('openapi', get_schema_view(
        title="Your Project",
        description="API for all things …"
    ), name='openapi-schema'),
    path('swaggerui/', TemplateView.as_view(
        template_name='swaggerUI.html',
        extra_context={'schema_url':'openapi-schema'}
    ), name='swagger-ui'),
    path('admin/', admin.site.urls),
    path('tweets/', include('tweets.urls')),
    path(('users/'), include('users.urls')),
    path('password/reset/', PasswordResetView.as_view()),
    path('password/reset/confirm/',
         PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('verify-email/',
          VerifyEmailView.as_view(), name='account_email_verification_sent'),
    path('resend-email/', ResendEmailVerificationView.as_view(), name='rest_resend_email'),

    path('token/refresh/', get_refresh_view().as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name="token_verify"),
    path("debug/", include("debug_toolbar.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


