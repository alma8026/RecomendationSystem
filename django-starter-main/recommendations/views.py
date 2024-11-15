from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Rating
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .recommendation_utils import get_data, calculate_similarity, get_recommendations, csr_matrix
from .content_based_utils import recommend_items_content, get_top_genres

@login_required
def movie_list(request):
    user = request.user
    movies = Movie.objects.all()
    
    # Obtén las puntuaciones del usuario para las películas
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

        # Create the stars display HTML
        stars_display = ''.join(['⭐' for _ in range(value)]) + ''.join(['☆' for _ in range(5 - value)])
        
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
    recommended_movies_objects = [Movie.objects.get(title=item) for item in recommended_movies]

    # Obtener datos para recomendaciones basadas en contenido
    user_ratings = Rating.objects.filter(user=user)
    if user_ratings.exists():
        recommended_content_movies = recommend_items_content(user_ratings)
        top_genres = get_top_genres(user_ratings)
    else:
        recommended_content_movies = []
        top_genres = []

    # Obtener detalles de las películas recomendadas basadas en contenido
    recommended_content_movies_objects = [Movie.objects.get(title=item) for item in recommended_content_movies]

    rated_movies = []
    user_ratings = Rating.objects.filter(user=user)
    user_rated_movies = Movie.objects.filter(id__in=user_ratings.values_list('movie_id', flat=True))

    for movie in user_rated_movies:
        rating = user_ratings.get(movie_id=movie.id).value
        filled_stars = '⭐' * rating
        empty_stars = '☆' * (5 - rating)
        stars_display = filled_stars + empty_stars
        rated_movies.append({
            'title': movie.title,
            'stars': stars_display
        })

    context = {
        'recommended_movies': recommended_movies_objects,
        'recommended_content_movies': recommended_content_movies_objects,
        'user_rated_movies': user_ratings,
        'rated_movies': rated_movies,
        'top_genres': top_genres,
    }

    return render(request, 'recommendations/recommendations.html', context)