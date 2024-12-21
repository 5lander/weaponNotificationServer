
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

#app_name = AppName

urlpatterns = [
    path('login/', views.loginPage, name='login'),
    path('register/', views.registerPage, name='register'),
    path('', views.home, name='home'),
    path('logout/', views.logoutUser, name='logout'),

    path('reset_password/',
         auth_views.PasswordResetView.as_view(template_name = "detection/password_reset.html"),
         name ='reset_password'),
    path('resetpasswordsent/',
         auth_views.PasswordResetDoneView.as_view(template_name = "detection/password_reset_sent.html"),
         name ='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name = "detection/password_reset_form.html"),
         name ='password_reset_confirm'),
    path('resetpasswordcomplete/',
         auth_views.PasswordResetCompleteView.as_view(template_name = "detection/password_reset_done.html"),
         name ='password_reset_complete'),
    path('alert/<uuid:pk>/',views.alert, name='alert'),         

]