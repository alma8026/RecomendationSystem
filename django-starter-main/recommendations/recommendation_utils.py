import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from scipy.spatial.distance import cosine
from django.contrib.auth.models import User
from .models import Movie, Rating

# Función para obtener los datos de calificaciones y películas
def get_data():
    movie_titles = list(Movie.objects.values_list('title', flat=True))
    user_ids = list(User.objects.values_list('id', flat=True))
    user_ratings = Rating.objects.all()
    
    ratings_matrix = pd.DataFrame(index=user_ids, columns=movie_titles).fillna(0).astype(float)
    
    for rating in user_ratings:
        ratings_matrix.at[rating.user.id, rating.movie.title] = float(rating.value)
    
    return ratings_matrix, movie_titles, user_ids

# Función para calcular la similitud entre usuarios
def calculate_similarity(matrix):
    num_users = matrix.shape[0]
    similarity_matrix = np.zeros((num_users, num_users))
    
    for i in range(num_users):
        for j in range(num_users):
            if i != j:
                similarity_matrix[i, j] = 1 - cosine(matrix[i].toarray().flatten(), matrix[j].toarray().flatten())
    
    return similarity_matrix

# Función para hacer recomendaciones basadas en usuarios
def recommend_items(user_index, user_item_matrix, similarity_matrix, top_n=5):
    user_ratings = user_item_matrix.iloc[user_index].values
    similar_users = similarity_matrix[user_index]
    
    pred_ratings = np.zeros(user_item_matrix.shape[1])
    
    for i in range(user_item_matrix.shape[1]):
        if user_ratings[i] == 0:  # Solo predecir para ítems no calificados
            pred_ratings[i] = np.dot(similar_users, user_item_matrix.iloc[:, i]) / np.sum(similar_users)
    
    # Obtener los ítems con mayor puntuación predicha
    recommended_indices = np.argsort(pred_ratings)[::-1][:top_n]
    recommended_movies = user_item_matrix.columns[recommended_indices]
    
    return recommended_movies

# Función para obtener recomendaciones y excluir películas ya calificadas
def get_recommendations(user_index, user_item_matrix, similarity_matrix, top_n=5):
    user_ratings = user_item_matrix.iloc[user_index]
    
    if user_ratings.sum() == 0:
        return []  # No hacer recomendaciones si el usuario no ha calificado ninguna película
    
    recommended_movies = recommend_items(user_index, user_item_matrix, similarity_matrix, top_n)
    
    # Excluir las películas ya calificadas
    recommended_movies_filtered = [movie for movie in recommended_movies if user_ratings[movie] == 0]
    
    return recommended_movies_filtered
