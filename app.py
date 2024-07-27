import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine
from faker import Faker
import random
from scipy.sparse import csr_matrix
import time
import matplotlib.pyplot as plt

# Inicializar Faker
fake = Faker()

# Configurar parámetros
num_users = 20
num_items = 40
min_rating = 1
max_rating = 5
density = 0.2  # Densidad para que los usuarios no califiquen todas las películas (20%)

# Datos de películas y géneros
movie_data = {
    'The Shawshank Redemption': ['Drama'],
    'The Godfather': ['Crime', 'Drama'],
    'The Dark Knight': ['Action', 'Crime', 'Drama'],
    'Pulp Fiction': ['Crime', 'Drama'],
    'Forrest Gump': ['Drama', 'Romance'],
    'The Lord of the Rings: The Return of the King': ['Action', 'Adventure', 'Drama'],
    'Inception': ['Action', 'Adventure', 'Sci-Fi'],
    'Fight Club': ['Drama'],
    'The Matrix': ['Action', 'Sci-Fi'],
    'The Empire Strikes Back': ['Action', 'Adventure', 'Sci-Fi'],
    'Interstellar': ['Adventure', 'Drama', 'Sci-Fi'],
    'The Green Mile': ['Drama', 'Fantasy'],
    'Gladiator': ['Action', 'Adventure', 'Drama'],
    'The Departed': ['Crime', 'Drama', 'Thriller'],
    'The Prestige': ['Drama', 'Mystery', 'Sci-Fi'],
    'The Lion King': ['Animation', 'Adventure', 'Drama'],
    'The Usual Suspects': ['Crime', 'Drama', 'Mystery'],
    'Schindler\'s List': ['Biography', 'Drama', 'History'],
    'The Silence of the Lambs': ['Crime', 'Drama', 'Thriller'],
    'The Shining': ['Drama', 'Horror'],
    'Se7en': ['Crime', 'Drama', 'Thriller'],
    'Saving Private Ryan': ['Drama', 'War'],
    'The Social Network': ['Biography', 'Drama'],
    'A Beautiful Mind': ['Biography', 'Drama'],
    'The Truman Show': ['Comedy', 'Drama', 'Sci-Fi'],
    'Whiplash': ['Drama', 'Music'],
    'Joker': ['Crime', 'Drama', 'Thriller'],
    'Parasite': ['Comedy', 'Drama', 'Thriller'],
    '1917': ['Drama', 'War'],
    'Jojo Rabbit': ['Comedy', 'Drama', 'War'],
    'Once Upon a Time in Hollywood': ['Comedy', 'Drama'],
    'Spider-Man: Into the Spider-Verse': ['Animation', 'Action', 'Adventure'],
    'Mad Max: Fury Road': ['Action', 'Adventure', 'Sci-Fi'],
    'Her': ['Drama', 'Romance', 'Sci-Fi'],
    'La La Land': ['Comedy', 'Drama', 'Music'],
    'Moonlight': ['Drama'],
    'The Grand Budapest Hotel': ['Adventure', 'Comedy', 'Drama'],
    'Django Unchained': ['Action', 'Drama', 'Western'],
    'The Hateful Eight': ['Crime', 'Drama', 'Western'],
    'The Big Lebowski': ['Comedy', 'Crime'],
    'The Revenant': ['Action', 'Adventure', 'Drama'],
    'Knives Out': ['Comedy', 'Crime', 'Drama']
}

# Convertir datos de películas a DataFrame
movie_titles = list(movie_data.keys())
genres = list(set(g for sublist in movie_data.values() for g in sublist))
genre_matrix = pd.DataFrame(0, index=movie_titles, columns=genres)

for movie, movie_genres in movie_data.items():
    for genre in movie_genres:
        genre_matrix.at[movie, genre] = 1

# Generar usuarios y películas aleatorios
user_ids = [fake.name() for _ in range(num_users)]
item_ids = random.sample(movie_titles, num_items)  # Elegir títulos de películas aleatorios

# Crear una matriz de calificaciones aleatorias
np.random.seed(0)
matrix = np.random.uniform(0, 1, (num_users, num_items))

# Aplicar una densidad a la matriz
mask = np.random.rand(num_users, num_items) < density
matrix[~mask] = 0

# Escalar los valores a [1, 5] y mantener los valores no calificados como 0
scaled_matrix = np.copy(matrix)
# Escalar las calificaciones en el rango [1, 5]
scaled_matrix[scaled_matrix > 0] = np.floor(scaled_matrix[scaled_matrix > 0] * (max_rating - min_rating) + min_rating + 1)
# Asegurarse de que las calificaciones estén en el rango [1, 5]
scaled_matrix = np.clip(scaled_matrix, min_rating, max_rating)
# Mantener los valores no calificados como 0
scaled_matrix[matrix == 0] = 0

# Crear DataFrame
df = pd.DataFrame(scaled_matrix, index=user_ids, columns=item_ids)
sparse_matrix = csr_matrix(df.values)

# Calcular la similitud entre usuarios
def calculate_similarity(matrix):
    num_users = matrix.shape[0]
    similarity_matrix = np.zeros((num_users, num_users))

    for i in range(num_users):
        for j in range(num_users):
            if i != j:
                similarity_matrix[i, j] = 1 - cosine(matrix[i].toarray().flatten(), matrix[j].toarray().flatten())
    
    return similarity_matrix

# Calcular la similitud entre películas
def calculate_movie_similarity(genre_matrix):
    return np.dot(genre_matrix.values, genre_matrix.values.T)

# Hacer recomendaciones basadas en contenido
def recommend_movies_content(user_ratings, genre_matrix, top_n=5):
    unrated_movies = [movie for movie in genre_matrix.index if user_ratings.get(movie, 0) == 0]
    movie_scores = np.zeros(len(unrated_movies))

    for idx, movie in enumerate(unrated_movies):
        movie_genre_vector = genre_matrix.loc[movie].values
        movie_score = 0

        # Sumamos las similitudes de las películas ya calificadas
        for rated_movie in user_ratings.index:
            if user_ratings[rated_movie] > 0:
                rated_movie_genre_vector = genre_matrix.loc[rated_movie].values
                movie_score += user_ratings[rated_movie] * np.dot(movie_genre_vector, rated_movie_genre_vector)
        
        movie_scores[idx] = movie_score
    
    # Obtener los ítems con mayor puntuación predicha
    recommended_indices = np.argsort(movie_scores)[::-1][:top_n]
    recommended_movies = np.array(unrated_movies)[recommended_indices]

    return recommended_movies

# Hacer recomendaciones basadas en usuarios
def recommend_items(user_index, user_item_matrix, similarity_matrix, top_n=5):
    user_ratings = user_item_matrix.iloc[user_index].values
    similar_users = similarity_matrix[user_index]
    
    # Calcular puntuaciones predichas
    pred_ratings = np.zeros(user_item_matrix.shape[1])
    
    for i in range(user_item_matrix.shape[1]):
        if user_ratings[i] == 0:  # Solo predecir para ítems no calificados
            pred_ratings[i] = np.dot(similar_users, user_item_matrix.iloc[:, i]) / np.sum(similar_users)
    
    # Obtener los ítems con mayor puntuación predicha
    recommended_indices = np.argsort(pred_ratings)[::-1][:top_n]
    recommended_movies = user_item_matrix.columns[recommended_indices]

    return recommended_movies

# Función para convertir rating a estrellas
def rating_to_stars(rating):
    try:
        rating = int(round(rating))  # Asegurarse de que rating sea un entero
        filled_stars = '★' * rating
        empty_stars = '☆' * (max_rating - rating)
        return filled_stars + empty_stars
    except ValueError:
        return 'Error'


# Medir el tiempo de ejecución para recomendaciones basadas en contenido y filtrado colaborativo
def main():
    # Calcular matrices de similitud
    start_time = time.time()
    similarity_matrix = calculate_similarity(sparse_matrix)
    collaborative_time = time.time() - start_time

    start_time = time.time()
    movie_similarity = calculate_movie_similarity(genre_matrix)
    content_time = time.time() - start_time

    # Seleccionar un usuario para recomendar
    user_index = 0
    user_name = df.index[user_index]

    # Obtener las películas calificadas por el usuario
    user_ratings = df.iloc[user_index]
    rated_movies = user_ratings[user_ratings > 0]

    # Obtener recomendaciones para el usuario
    recommended_items_collab = recommend_items(user_index, df, similarity_matrix)
    recommended_items_content = recommend_movies_content(user_ratings, genre_matrix)

    # Imprimir resultados
    print(f"Nombre del usuario: {user_name}")
    print("\nPelículas calificadas por él/ella:")
    if len(rated_movies) > 0:
        for movie, rating in rated_movies.items():
            stars = rating_to_stars(rating)
            print(f"{movie} --> {stars}")
    else:
        print("El usuario no ha calificado ninguna película.")

    print("\nRecomendaciones de películas (Filtrado Colaborativo):")
    if len(recommended_items_collab) > 0:
        for movie in recommended_items_collab:
            print(movie)
    else:
        print("No hay recomendaciones disponibles para el Filtrado Colaborativo.")

    print("\nRecomendaciones de películas (Filtrado Basado en Contenido):")
    if len(recommended_items_content) > 0:
        for movie in recommended_items_content:
            print(movie)
    else:
        print("No hay recomendaciones disponibles para el Filtrado Basado en Contenido.")

    # Graficar los tiempos de ejecución
    plt.bar(['Filtrado Colaborativo', 'Filtrado Basado en Contenido'], [collaborative_time, content_time])
    plt.ylabel('Tiempo de Ejecución (segundos)')
    plt.title('Tiempo de Ejecución por Algoritmo')
    plt.show()

# Ejecutar la función principal
if __name__ == "__main__":
    main()
