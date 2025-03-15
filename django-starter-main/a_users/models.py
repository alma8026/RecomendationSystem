from django.db import models
from django.contrib.auth.models import User
from recommendations.models import Movie
from django.templatetags.static import static

# No es necesario importar CustomList al principio del archivo

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField(max_length=20, null=True, blank=True)
    info = models.TextField(null=True, blank=True)
    favorites = models.ManyToManyField(Movie, blank=True, related_name='favorited_by')

    # Relación con CustomList. No es necesario importar CustomList arriba. Puedes usar la relación de la siguiente manera:
    custom_lists = models.ManyToManyField('a_users.CustomList', blank=True, related_name="profiles")

    def __str__(self):
        return str(self.user)

    @property
    def name(self):
        return self.displayname if self.displayname else self.user.username

    @property
    def avatar(self):
        return self.image.url if self.image else static("images/avatar.svg")

class CustomList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="custom_lists")
    title = models.CharField(max_length=255)
    movies = models.ManyToManyField(Movie, related_name="custom_lists", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def add_movie(self, movie):
        self.movies.add(movie)
        self.save()

    def remove_movie(self, movie):
        self.movies.remove(movie)
        self.save()
