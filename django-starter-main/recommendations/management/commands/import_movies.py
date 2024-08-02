import json
from django.core.management.base import BaseCommand
from recommendations.models import Movie, Genre

class Command(BaseCommand):
    help = 'Load movies from a JSON file into the database'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The path to the JSON file to be imported')

    def handle(self, *args, **options):
        json_file = options['json_file']
        try:
            with open(json_file, 'r') as file:
                data = json.load(file)
                
                for title, genres in data.items():
                    # Ensure genres exist in the database
                    genre_objects = []
                    for genre_name in genres:
                        genre, created = Genre.objects.get_or_create(name=genre_name)
                        genre_objects.append(genre)

                    # Create or get the movie
                    movie, created = Movie.objects.get_or_create(title=title)
                    
                    # Assign the genres to the movie
                    movie.genres.set(genre_objects)
                    movie.save()

                self.stdout.write(self.style.SUCCESS('Successfully imported movies from JSON file'))
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR('File not found'))
        except json.JSONDecodeError:
            self.stderr.write(self.style.ERROR('Error decoding JSON'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))
