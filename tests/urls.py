from django.urls import path, include

urlpatterns = [
    path("captcha/", include("django_tianai_captcha.urls")),
]
