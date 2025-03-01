from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Rating, Genre
from a_users.models import Profile
from math import floor, isclose
from django.db.models import Count, Avg
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .recommendation_utils import get_data, calculate_similarity, get_recommendations, csr_matrix
from .content_based_utils import recommend_items_content, get_top_genres

@login_required
def movie_list(request):
    user = request.user
    movies = Movie.objects.all()
    genres = Genre.objects.all()  # Obtenemos todos los géneros disponibles
    
    # Obtener parámetros de búsqueda y filtro
    search_query = request.GET.get('search', '').strip()
    genre_id = request.GET.get('genre', '').strip()
    
    # Filtrar películas
    if search_query:
        movies = movies.filter(title__icontains=search_query)  # Filtrar por título que contenga el término
    if genre_id:
        movies = movies.filter(genres__id=genre_id)  # Usa 'genres__id' porque el campo es 'genres'
    
    # Obtener puntuaciones del usuario para las películas
    user_ratings = Rating.objects.filter(user=user).values_list('movie_id', 'value')
    user_rated_movies = {movie_id: rating for movie_id, rating in user_ratings}
    
    # Preparar las estrellas llenas y vacías
    for movie in movies:
        movie_id = movie.id
        if movie_id in user_rated_movies:
            rating = user_rated_movies[movie_id]
            movie.stars_display = rating  # Solo necesitamos el número de estrellas llenas
        else:
            movie.stars_display = 0  # No ha sido calificada

    context = {
        'movies': movies,
        'user_rated_movies': user_rated_movies,
        'genres': genres,  # Para el filtro por género
    }
    return render(request, 'movies/movie_list.html', context)

@login_required
def rate_movie(request, movie_id):
    if request.method == 'POST':
        movie = get_object_or_404(Movie, id=movie_id)
        value = request.POST.get('rating')  # Get the rating from the form

        if value is not None:
            value = int(value)  # Convert to integer

            rating, created = Rating.objects.get_or_create(user=request.user, movie=movie, defaults={'value': value})
            if not created:
                rating.value = value
                rating.save()

        # Create the stars display HTML with images
        stars_display = ''.join(
            f'<span class="star-container"><img class="rate-stars" src="/static/images/star-filled.PNG" alt="Star Filled" class="star-img"></span>' for _ in range(value)
        ) + ''.join(
            f'<span class="star-container"><img class="rate-stars" src="/static/images/star-empty.PNG" alt="Star Empty" class="star-img"></span>' for _ in range(5 - value)
        )

        # Return the updated stars_display
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'stars_display': stars_display})

    return redirect('movie_list')


@login_required
def recommendations_view(request):
    # Obtener datos para recomendaciones colaborativas
    ratings_matrix, movie_titles, user_ids = get_data()
    user = request.user

    if user.id not in user_ids:
        return redirect('some_error_page')  # Redirigir si el usuario no está en la base de datos

    user_index = user_ids.index(user.id)
    user_item_matrix = ratings_matrix
    sparse_matrix = csr_matrix(user_item_matrix.values)
    similarity_matrix = calculate_similarity(sparse_matrix)
    recommended_movies = get_recommendations(user_index, user_item_matrix, similarity_matrix)

    # Obtener objetos Movie con datos adicionales
    recommended_movies_objects = [
        {'id': item.id, 'title': item.title, 'image_url': item.image_url} 
        for item in Movie.objects.filter(title__in=recommended_movies)
    ]

    # Obtener datos para recomendaciones basadas en contenido
    user_ratings = Rating.objects.filter(user=user)
    if user_ratings.exists():
        recommended_content_movies = recommend_items_content(user_ratings)
        top_genres = get_top_genres(user_ratings)  # Asegúrate de que esto devuelva objetos Genre
    else:
        recommended_content_movies = []
        top_genres = []

    # Obtener detalles de las películas recomendadas basadas en contenido
    recommended_content_movies_objects = [
        {'id': item.id, 'title': item.title, 'image_url': item.image_url} 
        for item in Movie.objects.filter(title__in=recommended_content_movies)
    ]

    # Obtener las películas calificadas por el usuario
    rated_movies = []
    user_rated_movies = Movie.objects.filter(id__in=user_ratings.values_list('movie_id', flat=True))

    for movie in user_rated_movies:
        # Obtener la calificación del usuario para esta película
        rating = user_ratings.get(movie_id=movie.id).value
        full_stars = int(floor(rating))  # Parte entera de la calificación
        has_half_star = rating - full_stars >= 0.5  # Determina si hay media estrella

        # Rutas de las imágenes de las estrellas
        filled_star_image = '/static/images/star-filled.PNG'
        empty_star_image = '/static/images/star-empty.PNG'
        half_star_image = '/static/images/star-half.PNG'

        # Generar las estrellas para la calificación
        stars_display = [filled_star_image] * full_stars
        if has_half_star:
            stars_display.append(half_star_image)
        stars_display += [empty_star_image] * (5 - len(stars_display))

        rated_movies.append({
            'id': movie.id,  # Asegurar que incluimos el ID de la película
            'title': movie.title,
            'image_url': movie.image_url,
            'stars': stars_display
        })

    # Contexto para la plantilla
    context = {
        'recommended_movies': recommended_movies_objects,
        'recommended_content_movies': recommended_content_movies_objects,
        'user_rated_movies': user_ratings,
        'rated_movies': rated_movies,
        'top_genres': top_genres,  # Lista de objetos Genre
    }

    return render(request, 'recommendations/recommendations.html', context)

@login_required
def movie_detail(request, movie_id):
    # Obtener la película
    movie = get_object_or_404(Movie, id=movie_id)
    
    # Intentamos obtener la calificación de la película para el usuario actual
    rating = Rating.objects.filter(user=request.user, movie=movie).first()
    
    # Si existe una calificación, la tomamos, si no, la ponemos a 0
    user_rating_value = float(rating.value) if rating else 0.0

    # Función auxiliar para generar las estrellas
    def generate_stars_display(rating_value):
        filled_star_image = '/static/images/star-filled.PNG'
        half_star_image = '/static/images/half-star.PNG'
        empty_star_image = '/static/images/star-empty.PNG'
        

        if rating_value > 0:
            # Determinar estrellas llenas, media estrella y vacías
            full_stars = int(floor(rating_value))  # Parte entera de la calificación
            fractional_part = rating_value - full_stars  # Parte decimal de la calificación
            has_half_star = 0.25 <= fractional_part < 0.75  # Verifica si hay media estrella

            # Crear la representación visual
            stars_display = ''.join(
                f'<span class="star-container"><img class="rate-stars w-6 h-6" src="{filled_star_image}" alt="Star Filled"></span>' 
                for _ in range(full_stars)
            )
            if has_half_star:
                stars_display += f'<span class="star-container"><img class="rate-stars w-6 h-6" src="{half_star_image}" alt="Half Star"></span>'
            stars_display += ''.join(
                f'<span class="star-container"><img class="rate-stars w-6 h-6" src="{empty_star_image}" alt="Star Empty"></span>' 
                for _ in range(5 - full_stars - (1 if has_half_star else 0))
            )
        else:
            stars_display = '<span class="star-container">No calificada</span>'
        
        return stars_display

    # Generar estrellas para la calificación del usuario
    stars_display = generate_stars_display(user_rating_value)

    # Calcular la calificación media de la película
    avg_rating = Rating.objects.filter(movie=movie).aggregate(Avg('value'))['value__avg'] or 0.0

    # Generar estrellas para la calificación media
    stars_display_avg = generate_stars_display(avg_rating)
    
    # Formatear las calificaciones como números con dos decimales
    user_rating_value_formatted = f"{user_rating_value:.2f}"
    avg_rating_formatted = f"{avg_rating:.2f}"
    
    # Convertir la duración a horas y minutos
    duration_minutes = movie.duration_minutes or 0
    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    duration_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
    
    # Obtener las plataformas en las que está disponible la película
    platforms = movie.platforms.all()

    # Obtener el trailer URL
    trailer_url = movie.trailer_url
    
    # Pasar la película, las estrellas generadas, la duración, plataformas y tráiler al contexto
    context = {
        'movie': movie,
        'stars_display': stars_display,
        'stars_display_avg': stars_display_avg,  # Calificación promedio visual
        'user_rating_value': user_rating_value_formatted,  # Calificación del usuario formateada
        'avg_rating_value': avg_rating_formatted,  # Calificación promedio formateada
        'duration_str': duration_str,
        'platforms': platforms,
        'trailer_url': trailer_url,
    }

    return render(request, 'movies/movie_detail.html', context)

def toggle_favorite(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    profile = Profile.objects.get(user=request.user)

    if movie in profile.favorites.all():
        profile.favorites.remove(movie)
        response = {
            "favorite_status": "removed",
        }
    else:
        profile.favorites.add(movie)
        response = {
            "favorite_status": "added",
        }

    return JsonResponse(response)