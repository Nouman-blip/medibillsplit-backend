# accounts/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action
from django.contrib.auth import logout
from .models import PrimaryAccount, Member
from .serializers import (
    PrimaryAccountSerializer,
    MemberSerializer,
    RegistrationSerializer,
    LoginSerializer
)

class PrimaryAccountViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing family accounts
    """
    queryset = PrimaryAccount.objects.all()
    serializer_class = PrimaryAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        account = self.get_object()
        serializer = MemberSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save(primary_account=account)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegistrationAPI(APIView):
    """
    API endpoint for user registration
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user_id': user.id,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPI(APIView):
    """
    API endpoint for user authentication
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            response = Response({
                'user_id': user.id,
                'email': user.email,
                'access': str(refresh.access_token),
            })
            response.set_cookie(
                'refresh_token', 
                str(refresh),
                httponly=True,
                secure=True,
                samesite='Lax'
            )
            return response
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)

class LogoutAPI(APIView):
    """
    API endpoint for user logout
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            response = Response(status=status.HTTP_205_RESET_CONTENT)
            response.delete_cookie('refresh_token')
            logout(request)
            return response
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)