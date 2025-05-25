"""
URL configuration for project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include,path
from tomikuvzpevnik.views import register,activate_account
from django.conf import settings

# from django.contrib.auth import views as auth_views

app_name = "tomikuvzpevnik"
urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("tomikuvzpevnik.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("accounts/create_account", register, name="sign_up"),
    path("accounts/activate/<uidb64>/<token>", activate_account, name="activate"),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()
