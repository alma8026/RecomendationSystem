from django.urls import path
from . import views

urlpatterns = [
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('rate/<int:movie_id>/', views.rate_movie, name='rate_movie'),
    path('movies/', views.movie_list, name='movie_list'),
    path('movie/<int:movie_id>/', views.movie_detail, name='movie_detail'),
    path('toggle_favorite/<int:movie_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('movie/<int:movie_id>/remove_rating/', views.remove_rating, name='remove_rating'),
    path('movies/<int:movie_id>/add_review/', views.add_review, name='add_review'),
]
