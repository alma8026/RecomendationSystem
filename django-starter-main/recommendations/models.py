from django.db import models
from django.contrib.auth.models import User

class Platform(models.Model):
    name = models.CharField(max_length=100)  # Nombre de la plataforma (por ejemplo, "Netflix", "Amazon Prime Video", etc.)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=255)
    genres = models.ManyToManyField('Genre')  # Relación con el modelo 'Genre'
    image_url = models.URLField(max_length=200, blank=True, null=True)  # Campo para la imagen
    description = models.TextField(blank=True, null=True)  # Campo para la descripción de la película
    platforms = models.ManyToManyField(Platform, blank=True)  # Relación con el modelo 'Platform'
    trailer_url = models.URLField(max_length=200, blank=True, null=True)  # URL del tráiler
    duration_minutes = models.PositiveIntegerField(blank=True, null=True)  # Duración de la película en minutos

    def __str__(self):
        return self.title

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    value = models.DecimalField(max_digits=5, decimal_places=2)  # Permite valores decimales

    class Meta:
        unique_together = ('user', 'movie')  # Asegura que un usuario no califique la misma película más de una vez

    def __str__(self):
        return f'{self.user.username} - {self.movie.title} - {self.value}'

class UserRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()  # Ajusta el campo de rating según tu necesidad

    class Meta:
        unique_together = ('user', 'movie')  # Asegura que no se repitan calificaciones para la misma película por el mismo usuario

    def __str__(self):
        return f'{self.user.username} - {self.movie.title} - {self.rating}'