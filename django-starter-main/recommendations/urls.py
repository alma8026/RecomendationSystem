from django.urls import path
from . import views

urlpatterns = [
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('rate/<int:movie_id>/', views.rate_movie, name='rate_movie'),
    path('movies/', views.movie_list, name='movie_list'),
]