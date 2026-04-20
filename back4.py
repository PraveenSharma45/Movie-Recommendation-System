import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ----------------------------------------------
# TMDB Configuration
# ----------------------------------------------
TMDB_API_KEY = "df9e2fedfa0e63b87e28de8d7695beb1"
BASE_URL = "https://api.themoviedb.org/3"

import requests

'''def get_movie_keywords(movie_id):#start
    """Fetch keywords for a movie using its TMDB ID"""
    search_url = f"https://api.themoviedb.org/3/movie/{movie_id}/keywords?api_key={TMDB_API_KEY}"
    res = requests.get(search_url)
    if res.status_code == 200:
        data = res.json()
        return data.get("keywords", [])
    return []#end'''
# ----------------------------------------------
# Fetch movie details from TMDB
# ----------------------------------------------
def get_movie_details(movie_name):
    search_url = f"{BASE_URL}/search/movie?api_key={TMDB_API_KEY}&query={movie_name}"
    res = requests.get(search_url).json()

    if not res.get("results"):
        print(f"❌ Movie '{movie_name}' not found.")
        return None

    movie_id = res["results"][0]["id"]
    details_url = f"{BASE_URL}/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,keywords"
    movie_data = requests.get(details_url).json()
    return movie_data


# ----------------------------------------------
# Extract feature text (genre / keywords / cast / combined)
# ----------------------------------------------
def extract_features(movie_data, mode="combined"):
    genres = [g["name"].replace(" ", "").lower() for g in movie_data.get("genres", [])]
    keywords = [k["name"].replace(" ", "").lower() for k in movie_data.get("keywords", {}).get("keywords", [])]
  


    if mode == "genre":
        return " ".join(genres)
    elif mode == "keywords":
        return " ".join(keywords)
    
    else:  # combined
        return " ".join(genres + keywords)


# ----------------------------------------------
# Get Similar Movies using TMDB data
# ----------------------------------------------
def get_similar_movies(movie_name, mode="combined", top_n=5, language="All"):

    # Handle list input from Streamlit multiselect
    if isinstance(mode, list):
        if len(mode) == 0:
            mode = "combined"
        else:
            mode = mode[0]

    print(f"\n🔍 Finding movies similar to '{movie_name}' using mode = {mode.upper()} ...")

    base_movie = get_movie_details(movie_name)
    if not base_movie:
        return [], None  # return empty list and None if movie not found

    base_features = extract_features(base_movie, mode)

    # ---------------------------
    # Fetch candidate movies dynamically
    # ---------------------------
    movie_titles, movie_tags, posters, vote_averages = [], [], [], []
    movie_ids_seen = set()  # avoid duplicates

    # Prepare lists of IDs for genre, cast, and keywords
    genre_ids = [g['id'] for g in base_movie.get('genres', [])] if mode in ["genre", "combined"] else []
   
    keyword_ids = [k['id'] for k in base_movie.get('keywords', {}).get('keywords', [])] if mode in ["keywords", "combined"] else []

    # Build discover URL based on mode

    discover_url = f"{BASE_URL}/discover/movie?api_key={TMDB_API_KEY}&with_original_language=en&page=1"

    if genre_ids:
        discover_url += "&with_genres=" + ",".join(map(str, genre_ids))
    
    if keyword_ids:
        discover_url += "&with_keywords=" + ",".join(map(str, keyword_ids))

    
   # Add language filter
    if language == "Hindi":
       discover_url += "&with_original_language=hi"
    elif language == "English":
       discover_url += "&with_original_language=en"


    # Fetch candidate movies from TMDB
    candidate_movies = requests.get(discover_url).json().get("results", [])

    
    # Loop through candidate movies and extract features
    for movie in candidate_movies:
        if movie['id'] == base_movie['id'] or movie['id'] in movie_ids_seen:
            continue
        try:
            details_url = f"{BASE_URL}/movie/{movie['id']}?api_key={TMDB_API_KEY}&append_to_response=credits,keywords"
            data = requests.get(details_url).json()

            tags = extract_features(data, mode)
            if tags.strip():
                movie_titles.append(data['title'])
                movie_tags.append(tags)
                posters.append(f"https://image.tmdb.org/t/p/w500{data.get('poster_path')}")
                vote_averages.append(data.get('vote_average', "N/A"))
                movie_ids_seen.add(data['id'])

                '''keywords_list = get_movie_keywords(movie['id'])#start
                if keywords_list:
                   import random
                   random.shuffle(keywords_list)  # mix them up
                   random_keywords = [k["name"] for k in keywords_list[:3]]
                   data["random_keywords"] = random_keywords
                else:
                   data["random_keywords"] = ["Not Available"]#end'''
        except Exception as e:
            print(f"Error fetching movie {movie.get('title')}: {e}")
            continue

    if not movie_tags:
        print("❌ No movies found for comparison.")
        return [], base_movie

    # ---------------------------
    # Compute similarity
    # ---------------------------
    tfidf = TfidfVectorizer(max_features=5000, stop_words='english')
    vectors = tfidf.fit_transform([base_features] + movie_tags)
    similarity = cosine_similarity(vectors)[0][1:]

    # Sort top_n movies
    sorted_indices = similarity.argsort()[::-1][:top_n]

    recommendations = []
    for i in sorted_indices:
        recommendations.append({
            "title": movie_titles[i],
            "poster_path": posters[i],
            "similarity_score": round(float(similarity[i]), 3),
            "genres": ", ".join([g["name"] for g in base_movie.get("genres", [])]),
            
            "vote_average": vote_averages[i]
        })
        
    return recommendations, base_movie
# ----------------------------------------------
# Main Function (for console use)
# ----------------------------------------------
if __name__ == "main":
    movie_name = input("🎥 Enter a movie name: ")
    print("Choose mode:")
    print("1. Genre only")
    print("2. Keywords only")
    
    print("3. Combined (Genre + Keywords)")

    mode_choice = input("Enter choice (1-3): ").strip()
    mode_map = {"1": "genre", "2": "keywords", "3": "combined"}
    mode = mode_map.get(mode_choice, "combined")

    recs = get_similar_movies(movie_name, mode)

    if not recs:
        print("⚠ No similar movies found.")
    else:
        print("\n🎯 Top Recommended Movies:")
        for i, m in enumerate(recs, 1):
            print(f"{i}. {m['title']} (Score: {m['similarity_score']})")
            print(f"   Poster: {m['poster']}")