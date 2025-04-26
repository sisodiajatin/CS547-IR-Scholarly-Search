"""
URL configuration for scholar_search project.

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
from django.urls import path
from search import views

urlpatterns = [
    # path("admin/", admin.site.urls),
    path("search/", views.search, name='search'),
    path("resps/", views.resps, name='resps'),
    path("users/signup/", views.signup, name='signup'),
    path("users/login/", views.login, name='login'),
    path('users/logout/', views.logout, name='logout'),
    path('users/profile/', views.profile, name='profile'),
]
