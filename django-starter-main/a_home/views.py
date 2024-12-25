from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from recommendations.models import Movie, Rating
from recommendations.content_based_utils import recommend_items_content, get_top_genres  # Importa la función para recomendaciones basadas en contenido
from recommendations.recommendation_utils import get_recommendations, get_data, csr_matrix, calculate_similarity

def home_view(request):
    user = request.user
    
    # Obtener datos para recomendaciones colaborativas
    ratings_matrix, movie_titles, user_ids = get_data()

    if user.id not in user_ids:
        return render(request, 'home.html')  # Redirigir si el usuario no está en la base de datos

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

    # Obtén las 4 películas con mejor puntuación promedio
    top_rated_movies = Movie.objects.annotate(avg_rating=Avg('rating__value')).order_by('-avg_rating')[:4]

    # Generar una representación de estrellas para cada película
    for movie in top_rated_movies:
        # Calcular la calificación media (puedes redondear a 1 decimal o cualquier formato que prefieras)
        avg_rating = movie.avg_rating or 0  # Si no tiene calificaciones, ponemos 0
        
        # Generar la representación en estrellas (esto lo haremos en el template)
        movie.stars_display = generate_star_display(avg_rating)
        movie.star_num = round(avg_rating, 2)
    
    # Pasa las listas filtradas al contexto
    context = {
        'common_movies': common_movies,
        'recommended_movies_objects': recommended_movies_objects,
        'recommended_content_movies_objects': recommended_content_movies_objects,
        'top_genres': top_genres,
        'top_rated_movies': top_rated_movies,
    }
    
    return render(request, 'home.html', context)

def generate_star_display(rating_value):
    """
    Genera una cadena HTML con estrellas llenas y vacías según el valor de la calificación.
    """
    full_stars = int(rating_value)
    half_star = 1 if rating_value % 1 >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    # Construir las estrellas llenas, medias y vacías con tamaño ajustado
    stars_html = ''.join(
        f'<img src="/static/images/star-filled.PNG" alt="Star Filled" class="star-img w-6 h-6" />' for _ in range(full_stars)
    )
    if half_star:
        stars_html += '<img src="/static/images/half-star.PNG" alt="Star Half" class="star-img w-6 h-6" />'
    stars_html += ''.join(
        f'<img src="/static/images/star-empty.PNG" alt="Star Empty" class="star-img w-6 h-6" />' for _ in range(empty_stars)
    )
    return stars_html