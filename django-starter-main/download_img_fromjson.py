import os
import json

def update_image_urls_in_json(json_file, output_json_file):
    # Abre el archivo JSON original y carga los datos
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    # Itera sobre cada película en el JSON
    for movie in data:
        title = movie.get('title', 'Unknown_Title')  # Usamos el título si existe
        
        # Cambiamos los espacios por guiones bajos y formateamos la ruta
        formatted_title = title.replace(' ', '_')  # Reemplaza los espacios por guiones bajos
        image_url = f"images/covers/{formatted_title}.webp"  # Genera la nueva URL
        
        # Actualizamos el campo "image_url" con la nueva ruta
        movie['image_url'] = image_url
    
    # Guardamos el archivo con el formato específico deseado
    with open(output_json_file, 'w', encoding='utf-8') as output_file:
        # Especificamos la indentación manualmente, sin que cambien los saltos de línea
        output_file.write("[\n")  # Añadimos una apertura de lista
        for i, movie in enumerate(data):
            json.dump(movie, output_file, ensure_ascii=False, separators=(',', ': '))
            if i < len(data) - 1:  # Si no es el último elemento, añadimos coma
                output_file.write(",\n")
            else:
                output_file.write("\n")
        output_file.write("]\n")  # Añadimos el cierre de lista

    print(f"Los datos han sido actualizados en {output_json_file}")

if __name__ == "__main__":
    # Nombre del archivo JSON original
    json_file = "movies_genres.json"  # Cambia esto por el nombre de tu archivo JSON original

    # Nombre del archivo JSON de salida
    output_json_file = "updated_movies_genres.json"  # Cambia esto si quieres otro nombre para el archivo de salida

    # Llamada a la función para actualizar las rutas de imagen
    update_image_urls_in_json(json_file, output_json_file)
