from django.db import connection
from .models import Movie, Genre

def get_movie_genre_matrix():
    # Ejecutar una consulta SQL directa para obtener la matriz de películas y géneros
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT m.title, g.name
            FROM recommendations_movie_genres mg
            JOIN recommendations_movie m ON mg.movie_id = m.id
            JOIN recommendations_genre g ON mg.genre_id = g.id
        """)
        rows = cursor.fetchall()

    # Procesar los resultados
    movie_genre_matrix = {}
    for movie_title, genre_name in rows:
        if movie_title not in movie_genre_matrix:
            movie_genre_matrix[movie_title] = []
        movie_genre_matrix[movie_title].append(genre_name)

    return movie_genre_matrix

def get_top_genres(user_ratings, top_n=5):
    # Generar un conjunto de géneros preferidos por el usuario
    preferred_genres = set()
    for rating in user_ratings:
        movie = Movie.objects.get(id=rating.movie_id)
        genres = movie.genres.all()
        if rating.value >= 4:  # Considerar películas con calificación 4 o 5 como relevantes
            preferred_genres.update([genre.name for genre in genres])

    # Obtener los géneros más frecuentes
    genre_count = {genre: 0 for genre in preferred_genres}
    for genre in preferred_genres:
        genre_count[genre] = sum(1 for rating in user_ratings if genre in Movie.objects.get(id=rating.movie_id).genres.values_list('name', flat=True))

    # Obtener los géneros más populares (top_n géneros más frecuentes)
    top_genres = sorted(genre_count.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # Ahora devolvemos objetos de tipo Genre, no solo los nombres
    # Creamos un queryset con los géneros más frecuentes
    genre_names = [genre for genre, count in top_genres]
    genres = Genre.objects.filter(name__in=genre_names)  # Filtrar por los nombres de los géneros más frecuentes
    return genres

def recommend_items_content(user_ratings, top_n=5):
    movie_genre_matrix = get_movie_genre_matrix()

    # Obtener los títulos de las películas que el usuario ya ha calificado
    rated_movie_titles = {Movie.objects.get(id=rating.movie_id).title for rating in user_ratings}

    # Generar un conjunto de géneros preferidos por el usuario
    preferred_genres = set()
    for rating in user_ratings:
        movie = Movie.objects.get(id=rating.movie_id)
        genres = movie.genres.all()
        if rating.value >= 4:  # Considerar películas con calificación 4 o 5 como relevantes
            preferred_genres.update([genre.name for genre in genres])

    if not preferred_genres:
        return []  # No hay géneros preferidos si el conjunto está vacío

    # Calcular la relevancia de cada película basada en los géneros preferidos
    movie_scores = {}
    for movie, genres in movie_genre_matrix.items():
        if movie in rated_movie_titles:
            continue  # Excluir las películas ya calificadas

        score = sum(1 for genre in genres if genre in preferred_genres)
        movie_scores[movie] = score

    # Obtener las películas con mayor puntuación
    recommended_movies = sorted(movie_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    recommended_titles = [movie for movie, score in recommended_movies]

    return recommended_titles
