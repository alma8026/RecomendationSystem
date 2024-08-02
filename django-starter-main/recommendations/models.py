from django.db import models
from django.contrib.auth.models import User

class Movie(models.Model):
    title = models.CharField(max_length=255, unique=True)
    genres = models.ManyToManyField('Genre')

    def __str__(self):
        return self.title

class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    value = models.IntegerField()  # Debe permitir valores enteros

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