from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from recommendations.models import Movie, Rating
from recommendations.content_based_utils import recommend_items_content, get_top_genres  # Importa la función para recomendaciones basadas en contenido
from recommendations.recommendation_utils import get_recommendations, get_data, csr_matrix, calculate_similarity

@login_required
def home_view(request):
    user = request.user
    
    # Obtener datos para recomendaciones colaborativas
    ratings_matrix, movie_titles, user_ids = get_data()

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

    # Encontrar películas comunes
    common_movies_set = set(recommended_movies) & set(recommended_content_movies)
    common_movies = [Movie.objects.get(title=item) for item in common_movies_set]

    # Filtrar las películas comunes de las listas originales
    recommended_movies_objects = [movie for movie in recommended_movies_objects if movie not in common_movies]
    recommended_content_movies_objects = [movie for movie in recommended_content_movies_objects if movie not in common_movies]

    # Pasa las listas filtradas al contexto
    context = {
        'common_movies': common_movies,
        'recommended_movies_objects': recommended_movies_objects,
        'recommended_content_movies_objects': recommended_content_movies_objects,
    }
    
    return render(request, 'home.html', context)