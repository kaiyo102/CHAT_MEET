from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.login_chat, name="login_chat"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('home/', views.home, name="home"),
    path('signup/', views.signup, name="signup"),
    path('search/', views.search, name="search"),
    path('create_room/<str:username>/', views.create_room, name="create_room"),
    path('userpage/', views.userpage, name="userpage"),
    path('mainmeetingpage/', views.mainmeetingpage, name="mainmeetingpage"),
    path('meeting/', views.meeting, name="meeting"),
]