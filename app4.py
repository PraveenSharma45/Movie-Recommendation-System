# app.py
# app.py

# app.py


import streamlit as st
import pandas as pd
import requests
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from back4 import get_movie_details, get_similar_movies

st.set_page_config(page_title="🎬 TMDB Movie Recommender", layout="centered")

with st.sidebar:
    st.header("⚙ Settings")

    # Number of recommendations
    num_recommendations = st.slider(
        "How many recommendations to show",
        min_value=1, max_value=20, value=9
    )

    

st.title("🎬 TMDB Smart Movie Recommender")
st.caption("Get AI-powered movie recommendations using TMDB API + TF-IDF similarity")

movie_name = st.text_input("Enter a movie name:", placeholder="e.g. Inception")


st.sidebar.header("Choose similarity attributes")
selected_attributes = st.sidebar.multiselect(
    "Select attributes to compare:",
    ["genre", "keyword"],
    default=["genre", "keyword"]
)


st.sidebar.header("Select Language")
language = st.sidebar.radio(
    "Choose movie language:",
    ("All", "Hindi", "English")
)


if st.button("Recommend"):
    with st.spinner("Fetching recommendations..."):
        
        
        recs, main_movie  = get_similar_movies(movie_name, selected_attributes, num_recommendations, language)

        if not recs or not main_movie:
           st.error("❌ Movie not found. Try another movie name.")
        else:
           title = main_movie.get("title", "Unknown Movie")
           st.success(f"Top recommendations based on: {title}")

         # 🎞 Movie details section
           st.subheader(f"🎬 Movie Details: {title}")

        # Genres
           genres = [g["name"] for g in main_movie.get("genres", [])]
           st.write("*Genres:*", ", ".join(genres) if genres else "Not available")

         # Keywords
           keywords = main_movie.get("keywords", {}).get("keywords", [])
           keyword_names = [k["name"] for k in keywords] if keywords else []
           st.write("*Keywords:*", ", ".join(keyword_names) if keyword_names else "Not available")


           st.markdown("---")  # line separator
            # Define how many movies per row
        movies_per_row = 5

        for i in range(0, len(recs), movies_per_row):
            cols=st.columns(movies_per_row)
            for j, col in enumerate(cols):
                if i + j < len(recs):
                    movie = recs[i + j]
                    with col:
                        if movie["poster_path"]:
                          st.image(f"https://image.tmdb.org/t/p/w200{movie['poster_path']}")
                          st.markdown(f"{movie['title']}")
                          #st.caption(movie["genres"])
                          if "keyword" in selected_attributes:
                                    keywords_data = movie.get("keywords", {}).get("keywords", [])
                                    keyword_names = [k["name"] for k in keywords_data if "name" in k]
                                    if keyword_names:
                                        random_keywords = random.sample(keyword_names, min(5, len(keyword_names)))
                                        st.caption("Keywords: " + ", ".join(random_keywords))
                                    else:
                                        st.caption("Keywords: Not available")
                          else:
                                st.caption("Genres: " + movie["genres"])

                          rating = movie.get("vote_average") or "N/A"
                          st.write(f"Rating: {rating}")
                
            