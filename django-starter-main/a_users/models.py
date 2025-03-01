from django.db import models
from django.contrib.auth.models import User
from recommendations.models import Movie
from django.templatetags.static import static

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    displayname = models.CharField(max_length=20, null=True, blank=True)
    info = models.TextField(null=True, blank=True)
    favorites = models.ManyToManyField(Movie, blank=True, related_name='favorited_by')  # 🔹 Cambio aquí
    
    def __str__(self):
        return str(self.user)
    
    @property
    def name(self):
        return self.displayname if self.displayname else self.user.username
    
    @property
    def avatar(self):
        return self.image.url if self.image else static("images/avatar.svg")
