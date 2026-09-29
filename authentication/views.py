from django.core.cache import cache
from .authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate, login, logout,  get_user_model
from datetime import datetime, timedelta
from .serializers import ObtainTokenSerializer
from django.http import JsonResponse
from users.models import User
from django.views.decorators.http import require_http_methods
from django.conf import settings
import json


User = get_user_model()

@api_view(['POST'])
@require_http_methods(['POST'])
@permission_classes([AllowAny])
def sign_in(request):
    """ LOGIN """
    data = json.loads(request.body)
    serializer = ObtainTokenSerializer(data=data)
    if serializer.is_valid():
        user_qs = User.objects.filter(email = data['email'])
        user = user_qs.first()
        user_auth = authenticate(request, username = data['email'], password=data['password'])

        if user and user_auth and not user.is_verified:
            current_user = {
                "id": user.id,
                "username": user.first_name,
                "email": user.email,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin
            }
            return JsonResponse({
                "error": "user is not verified", "CurrentUser": current_user
            }, status = 400)
        if user.is_active == False:
            return JsonResponse({
                "error": "user is not active"
            }, status = 400)
        if user_auth:
            login(request, user)
            # create jwt token 
            jwt_token = str(JWTAuthentication.create_jwt(user))

            # build current user information
            current_user = {
                "id": user.pk,
                "username": user.first_name,
                "email": user.email,
                "is_verified": user.is_verified,
                "is_admin": user.is_admin
            }

            # cache the current user details
            cache.set('CurrentUser', current_user)

            # update last expiration time
            user.token_last_expired = datetime.now() + timedelta(hours=settings.JWT_CONF['TOKEN_LIFETIME_HOURS'])
            user.save()

            return JsonResponse({
                "message": "login successfully", "token":jwt_token, "CurrentUser":current_user
            },status=200)
    return JsonResponse({"error": serializer.errors}, status=400)


@api_view(['POST'])
@require_http_methods(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    try:
        logout(request)
        return JsonResponse({
            "message": 'logout successfully'
        },status=200)

    except AttributeError:
        return JsonResponse({
            "error": "user not authenticated "
        },status=200)