from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from recommendations.content_based_utils import recommend_items_content, get_top_genres
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from recommendations.models import Rating, Movie
from a_users.models import CustomList
from django.contrib import messages
from .forms import *

@login_required
def profile_view(request, username=None):
    if username:
        profile = get_object_or_404(User, username=username).profile
    else:
        try:
            profile = request.user.profile
        except:
            return redirect('account_login')

    # Contar el número de calificaciones realizadas por el usuario
    rating_count = Rating.objects.filter(user=request.user).count()

    # Calcular el número total de horas que ha visto el usuario
    rated_movies = Rating.objects.filter(user=request.user)  # Obtener las calificaciones del usuario
    total_minutes = sum(rating.movie.duration_minutes for rating in rated_movies)  # Sumar la duración total en minutos
    hours = total_minutes // 60  # Obtener las horas enteras
    minutes = total_minutes % 60  # Obtener los minutos restantes

    total_hours = f"{hours}h {minutes}min"  # Guardar el resultado en total_hours

    favorite_movies = profile.favorites.all()  # Obtener las películas favoritas
    favorite_movies_count = favorite_movies.count()

    # Obtener recomendaciones basadas en contenido y los géneros principales del usuario
    user_ratings = Rating.objects.filter(user=request.user)
    if user_ratings.exists():
        recommended_content_movies = recommend_items_content(user_ratings)
        top_genres = get_top_genres(user_ratings)
    else:
        recommended_content_movies = []
        top_genres = []

    # Obtener las listas personalizadas del usuario
    custom_lists = profile.custom_lists.all()  # Obtener todas las listas personalizadas asociadas al perfil

    return render(request, 'a_users/profile.html', {
        'profile': profile,
        'favorite_movies': favorite_movies,
        'rating_count': rating_count,
        'favorite_movies_count': favorite_movies_count,
        'total_hours': total_hours,  # Pasar las horas al contexto
        'recommended_content_movies': recommended_content_movies,  # Pasar recomendaciones
        'top_genres': top_genres,  # Pasar géneros principales
        'custom_lists': custom_lists  # Pasar las listas personalizadas
    })

@login_required
def custom_lists(request):
    user_profile = request.user.profile  # Obtiene el perfil del usuario
    if request.method == 'POST':
        title = request.POST.get('title')  # Obtiene el título de la lista desde el formulario
        if title:
            # Crear una nueva lista personalizada y asociarla al usuario
            new_list = CustomList.objects.create(user=request.user, title=title)
            user_profile.custom_lists.add(new_list)  # Agregar la lista al perfil del usuario
            return redirect('profile')  # Redirige al perfil del usuario
    
    # Si no es un POST, simplemente mostrar las listas del usuario
    return render(request, 'a_users/profile.html', {'user_profile': user_profile})

@login_required
def add_movie_to_list(request, list_id):
    # Obtener la lista personalizada seleccionada
    custom_list = get_object_or_404(CustomList, id=list_id, user=request.user)

    if request.method == 'POST':
        movie_id = request.POST.get('movie')
        if movie_id:
            # Obtener la película seleccionada
            movie = get_object_or_404(Movie, id=movie_id)
            # Agregar la película a la lista
            custom_list.add_movie(movie)
    
    return redirect('profile')  # Redirigir al perfil después de agregar la película

@login_required
def remove_movie_from_list(request, list_id, movie_id):
    # Obtén la lista personalizada y la película
    custom_list = get_object_or_404(CustomList, id=list_id, user=request.user)
    movie = get_object_or_404(Movie, id=movie_id)

    # Elimina la película de la lista
    custom_list.movies.remove(movie)

    # Redirige de vuelta al perfil del usuario
    return redirect('profile')  # Asegúrate de que esta URL esté definida en tus urls.py

@login_required
def remove_list(request, list_id):
    # Obtener la lista personalizada
    custom_list = get_object_or_404(CustomList, id=list_id, user=request.user)

    # Eliminar la lista
    custom_list.delete()

    # Redirigir al perfil después de eliminar la lista
    return redirect('profile')  # Asegúrate de que esta URL esté definida en tus urls.py


@login_required
def profile_edit_view(request):
    form = ProfileForm(instance=request.user.profile)  
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
        
    if request.path == reverse('profile-onboarding'):
        onboarding = True
    else:
        onboarding = False
      
    return render(request, 'a_users/profile_edit.html', { 'form':form, 'onboarding':onboarding })


@login_required
def profile_settings_view(request):
    return render(request, 'a_users/profile_settings.html')


@login_required
def profile_emailchange(request):
    
    if request.htmx:
        form = EmailForm(instance=request.user)
        return render(request, 'partials/email_form.html', {'form':form})
    
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)

        if form.is_valid():
            
            # Check if the email already exists
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.warning(request, f'{email} is already in use.')
                return redirect('profile-settings')
            
            form.save() 
            
            # Then Signal updates emailaddress and set verified to False
            
            # Then send confirmation email 
            send_email_confirmation(request, request.user)
            
            return redirect('profile-settings')
        else:
            messages.warning(request, 'Form not valid')
            return redirect('profile-settings')
        
    return redirect('home')


@login_required
def profile_emailverify(request):
    send_email_confirmation(request, request.user)
    return redirect('profile-settings')


@login_required
def profile_delete_view(request):
    user = request.user
    if request.method == "POST":
        logout(request)
        user.delete()
        messages.success(request, 'Account deleted, what a pity')
        return redirect('home')
    
    return render(request, 'a_users/profile_delete.html')