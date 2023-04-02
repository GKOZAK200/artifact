from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register', views.register_request, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('search/', views.search_media, name='search_media'),
    path('add-to-list/', views.add_to_list, name='add_to_list'),
    path('remove-from-list/<int:medialist_id>/<int:media_id>/', views.remove_from_list, name='remove_from_list'),
    path('add-rating/', views.add_rating, name='add_rating'),
    path('recommend/', views.recommend_media, name='recommend_media'),
]
