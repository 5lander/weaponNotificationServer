from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.loginPage, name='login'),
    path('register/', views.registerPage, name='register'),
    path('', views.home, name='home'),
    path('logout/', views.logoutUser, name='logout'),

    # Password Reset con templates personalizados
    path('reset_password/',
         auth_views.PasswordResetView.as_view(
             template_name='detection/password_reset.html',
             email_template_name='detection/password_reset_email.html',
             subject_template_name='detection/password_reset_subject.txt',
             html_email_template_name='detection/password_reset_email.html',
         ),
         name='reset_password'),
    
    path('resetpasswordsent/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='detection/password_reset_sent.html'
         ),
         name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='detection/password_reset_form.html'
         ),
         name='password_reset_confirm'),
    
    path('resetpasswordcomplete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='detection/password_reset_done.html'
         ),
         name='password_reset_complete'),
    
    path('alert/<uuid:pk>/', views.alert, name='alert'),         
]