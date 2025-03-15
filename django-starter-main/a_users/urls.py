from django.urls import path
from a_users.views import *

urlpatterns = [
    path('', profile_view, name="profile"),
    path('edit/', profile_edit_view, name="profile-edit"),
    path('onboarding/', profile_edit_view, name="profile-onboarding"),
    path('settings/', profile_settings_view, name="profile-settings"),
    path('emailchange/', profile_emailchange, name="profile-emailchange"),
    path('emailverify/', profile_emailverify, name="profile-emailverify"),
    path('delete/', profile_delete_view, name="profile-delete"),
    path('custom-lists/', custom_lists, name='custom_lists'),  # Ruta para ver y crear listas personalizadas
    path('add_movie_to_list/<int:list_id>/', add_movie_to_list, name='add_movie_to_list'),
    path('remove_movie_from_list/<int:list_id>/<int:movie_id>/', remove_movie_from_list, name='remove_movie_from_list'),
    path('remove_list/<int:list_id>/', remove_list, name='remove_list'),
]