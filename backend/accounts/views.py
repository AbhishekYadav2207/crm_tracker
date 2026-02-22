from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import MyTokenObtainPairSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    # queryset = User.objects.all() # Unnecessary as we override get_object
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class RegisterCHCAdminView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def get_permissions(self):
        from chc.views import IsGovtAdmin
        return [permissions.IsAuthenticated(), IsGovtAdmin()]

    def perform_create(self, serializer):
        serializer.save(role='CHC_ADMIN')

from rest_framework.views import APIView

class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        new_password = request.data.get("new_password")
        if not new_password:
            return Response({"error": "New password is required"}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({"message": "Password changed successfully", "status": "success"}, status=status.HTTP_200_OK)

class CHCAdminListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_permissions(self):
        from chc.views import IsGovtAdmin
        return [permissions.IsAuthenticated(), IsGovtAdmin()]

    def get_queryset(self):
        return User.objects.filter(role='CHC_ADMIN').order_by('id')

class RemoveCHCAdminView(APIView):
    def get_permissions(self):
        from chc.views import IsGovtAdmin
        return [permissions.IsAuthenticated(), IsGovtAdmin()]

    def delete(self, request, pk, *args, **kwargs):
        user = generics.get_object_or_404(User, pk=pk, role='CHC_ADMIN')
        user.delete()
        return Response({"message": "CHC Admin removed successfully"}, status=status.HTTP_204_NO_CONTENT)
