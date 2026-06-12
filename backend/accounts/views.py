from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


def _serialize_user(user):
	return {
		"id": user.id,
		"email": user.email,
		"full_name": user.full_name,
		"phone_number": user.phone_number,
		"is_active": user.is_active,
		"is_staff": user.is_staff,
	}


class AuthCSRFView(APIView):
	permission_classes = [permissions.AllowAny]
	authentication_classes = []

	@ensure_csrf_cookie
	def get(self, request):
		return Response({"success": True, "data": {"csrf": "ok"}})


class AuthLoginView(APIView):
	permission_classes = [permissions.AllowAny]
	authentication_classes = []

	def post(self, request):
		email = str(request.data.get("email", "")).strip().lower()
		password = str(request.data.get("password", ""))

		if not email or not password:
			return Response(
				{
					"success": False,
					"error": {
						"code": "invalid_credentials",
						"message": "Email and password are required.",
					},
				},
				status=status.HTTP_400_BAD_REQUEST,
			)

		user = authenticate(request=request, username=email, password=password)
		if not user:
			return Response(
				{
					"success": False,
					"error": {
						"code": "invalid_credentials",
						"message": "Invalid email or password.",
					},
				},
				status=status.HTTP_401_UNAUTHORIZED,
			)

		if not user.is_active:
			return Response(
				{
					"success": False,
					"error": {
						"code": "account_inactive",
						"message": "This account is inactive.",
					},
				},
				status=status.HTTP_403_FORBIDDEN,
			)

		login(request, user)
		return Response({"success": True, "data": _serialize_user(user)})


class AuthLogoutView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		logout(request)
		return Response({"success": True, "data": {"logged_out": True}})


class AuthMeView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def get(self, request):
		return Response({"success": True, "data": _serialize_user(request.user)})
