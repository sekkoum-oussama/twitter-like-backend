import email
from email.policy import default
from django.conf import settings
from django.db.models import Q
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.serializers import HyperlinkedModelSerializer, HyperlinkedIdentityField
from dj_rest_auth.serializers import UserDetailsSerializer, PasswordResetSerializer, LoginSerializer, PasswordResetConfirmSerializer
from rest_framework import exceptions
from django.urls import exceptions as url_exceptions
from django.utils.translation import gettext_lazy as _
from users.forms import CustomAllAuthPasswordResetForm
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework import status
from allauth.account.models import EmailAddress
from django.utils.encoding import force_str

User = get_user_model()

class UserDetailSerializer(UserDetailsSerializer, HyperlinkedModelSerializer):
    url = HyperlinkedIdentityField(view_name='profile-detail', lookup_field='username')

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'avatar', 'cover', 'bio', 'date_joined', 'location', 'date_birth')

    def to_representation(self, instance):
        rep= super().to_representation(instance)
        user = self.context.get("request").user
        rep["followers"] = instance.followers.count()
        rep["following"] = instance.following.count()
        if user.is_authenticated and  user.id != instance.id:
            rep["is_following"] = user.following.filter(id=instance.id).exists()
        return rep
        
    def validate_username(self, value):
        request = self.context.get("request")
        if request.user.username == value:
            return value
        default_validator = super().validators['username']
        try:
            default_validator(value)
        except serializers.ValidationError as e:
            raise e
        return value

    def update(self, instance, validated_data):
        files = self.context["files"]
        avatar = files.get("avatar")
        if avatar:
            instance.avatar = avatar
        cover = files.get("cover")
        if cover:
            instance.cover = cover
        return super().update(instance, validated_data)
        


class UserFollowersSerializer(HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='profile-detail', lookup_field='username')
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'avatar', 'bio')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        req = self.context.get('request')
        followers_list = list(instance._prefetched_objects_cache["followers"])
        ret["is_following"] = req.user.id in (profile.id for profile in followers_list)
        return ret

class CustomPasswordResetSerializer(PasswordResetSerializer):
    def validate_email(self, value):
        #Check if email exists
        try:
            User.objects.get(email__iexact=value)
        except User.DoesNotExist:
            raise NotFound()
        # Check if email is activated
        try:
            EmailAddress.objects.get(email__iexact=value, verified=True)
        except EmailAddress.DoesNotExist:
            raise serializers.ValidationError()
        # use the custom reset form
        self.reset_form = CustomAllAuthPasswordResetForm(data=self.initial_data)
        if not self.reset_form.is_valid():
            raise serializers.ValidationError(self.reset_form.errors)

        return value


class CustomPasswordResetConfirmSerializer(PasswordResetConfirmSerializer):
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)
    email = serializers.EmailField()
    token = serializers.CharField()
    uid = None
    def validate(self, attrs):
        if 'allauth' in settings.INSTALLED_APPS:
            from allauth.account.forms import default_token_generator
            from allauth.account.utils import url_str_to_user_pk as uid_decoder
        else:
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_decode as uid_decoder

        # get the user with email
        try:
            self.user = User.objects.get(email__iexact=attrs['email'])
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError({'email': ['Invalid email address']})


        if not default_token_generator.check_token(self.user, attrs['token']):
            raise ValidationError({'token': ['Invalid value']})

        self.custom_validation(attrs)
        # Construct SetPasswordForm instance
        self.set_password_form = self.set_password_form_class(
            user=self.user, data=attrs,
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)

        return attrs

class CustomLoginSerializer(LoginSerializer):
    def get_auth_user(self, username, email, password):
        """
        Added the try block, to check if the user with given Email or Username exists.
        """
        try:
            User.objects.get(Q(email__iexact=email) | Q(username__iexact=username))
        except User.DoesNotExist:
            msg = _('This user does not exist')
            raise exceptions.ValidationError(msg)
        if 'allauth' in settings.INSTALLED_APPS:

            # When `is_active` of a user is set to False, allauth tries to return template html
            # which does not exist. This is the solution for it. See issue #264.
            try:
                return self.get_auth_user_using_allauth(username, email, password)
            except url_exceptions.NoReverseMatch:
                msg = _('Unable to log in with provided credentials.')
                raise exceptions.ValidationError(msg)
        return self.get_auth_user_using_orm(username, email, password)

    def validate(self, attrs):
        username = attrs.get('username')
        email = attrs.get('email')
        password = attrs.get('password')
        user = self.get_auth_user(username, email, password)

        if not user:
            msg = _('Wrong password')
            raise exceptions.ValidationError(msg)

        # Did we get back an active user?
        self.validate_auth_user_status(user)

        # If required, is the email verified?
        if 'dj_rest_auth.registration' in settings.INSTALLED_APPS:
            self.validate_email_verification_status(user)

        attrs['user'] = user
        return attrs