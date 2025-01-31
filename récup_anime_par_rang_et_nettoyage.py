import requests
import pandas as pd
import ast

#Comme l'API ne nous permet pas de récupérer les animes en groupe à travers leur ID, on récupère la liste des animés et leur caractéristiques à partir de leur le rang, dans l'ordre décroissant décroissant (en prenant les 100 1ers rangs, puis les 100 rangs suivants ainsi de suite...)

all_anime = [] 
nbr_needed = 27490  #Total number of anime on MAL as of 13/11/2024 (obtained by looking directly on the site of myanimelist)

ID = {'X-MAL-CLIENT-ID': 'c2db532c391bf31339ffd6afa650d528'} #id client obtenu après s'être inscrit sur My Anime List et avoir fait une demande
url = 'https://api.myanimelist.net/v2/anime/ranking'
parameters = {
    'ranking_type': 'all',  
    'limit': 100,  # Max limit per request, divides the total number of anime on mal
    'fields': 'id,title,mean,start_date,end_date,rank,popularity,num_list_users,num_scoring_users,nsfw,media_type,status,num_episodes,start_season,broadcast,source,average_episode_duration,rating'
}

k = 0  # offset but also the number of times the loop is used that is 27490/100 here

# Loop until we've collected the target number of anime
while k < nbr_needed:
    parameters['offset'] = k
    mal = requests.get(url, headers=ID, params=parameters)

    
    if mal.status_code == 200: # Check if the request is successful
        data = mal.json()
        all_anime.extend(data['data'])
        k += parameters['limit']

        print(str(len(all_anime)) + " collected for the moment...")
    
        if len(all_anime) >= nbr_needed:
            print("the total number of anime collected is " + str(len(all_anime)))
            break
    else :
        print("cannot retrieve more than " + str(len(all_anime))) 
        break

anime_data = pd.DataFrame(all_anime) 
print(anime_data.head(2))

print(anime_data.head())
print(anime_data.info())

#On voit que le dataframe est constitué du rang des animé et d'un "node", un dictionnaire qui contient toutes les caractéristiques de chaque anime.
#Il faut donc extraire chaque élément du dictionnaire node pour en faire des colonnes à part entière

# On extrait toutes les clés du dictionnaire 'node' et on les transforme en colonnes du dataframe
anime_data['node'] = anime_data['node'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)    
keys = set().union(*(d.keys() for d in anime_data['node'] if isinstance(d, dict)))
for y in keys:
    anime_data[f'{y}'] = anime_data['node'].apply(lambda x: x.get(y) if isinstance(x, dict) else None)

# On convertit les colonnes contenant des dictionnaires en chaînes
for column in anime_data.columns:
    if anime_data[column].map(type).eq(dict).any():
        anime_data[column] = anime_data[column].apply(lambda x: str(x) if isinstance(x, dict) else x)

print(anime_data.head())

#On supprime la colonne node qui n'apporte plus d'info
anime_data = anime_data.drop(columns=['node'])

#On vérifie s'il y a des doublons
nbr_doublons = anime_data.duplicated().sum()
print(f"Il y a {nbr_doublons} doublons")

#On supprime les colonnes qui ne serviront pas pour la recommendation
anime_data=anime_data.drop(columns=['main_picture','broadcast','start_season','end_date'],axis=1)
pd.set_option('display.max_columns', None)
print(anime_data.head())

#On regarde combien de valeurs NaN il y a dans chaque colonne
for i in anime_data.columns:
    k = anime_data[i].isna().sum()
    print(f"Le nombre de NaN dans la colonne '{i}' est : {k}")

#On gère les différents types de NaN
anime_data['source'] = anime_data['source'].fillna('source_inconnue')
anime_data['rating'] = anime_data['source'].fillna('rating_inconnu')
anime_data['mean'] = anime_data['mean'].fillna(0)
anime_data = anime_data.dropna(subset=['rank'])

#On veut uniquement garder l'année dans la colonne start_date
anime_data['start_date'] = pd.to_datetime(anime_data['start_date'], errors='coerce')  
anime_data['start_year'] = anime_data['start_date'].dt.year  
anime_data=anime_data.drop(columns=['start_date'],axis=1)

anime_data = anime_data.dropna(subset=['start_year'])

#On vérifie qu'il n'y a plus de NaN
nbr_nan = anime_data.isna().sum().sum()
print(f"Il reste {nbr_nan} NaN")

#On ne garde que les colonnes numériques pour calculer la matrice de correlation
anime_data_num = anime_data.select_dtypes(include=["number"])
# Calcul de la matrice de corrélation
print(anime_data_num.corr())

#On sauvegarde le DataFrame en fichier CSV local
local_file_path = "anime_data.csv"
anime_data.to_csv(local_file_path, index=False)
print(f"Fichier CSV sauvegardé localement : {local_file_path}")
