# Data processing functions for reader_and_genre_preference.ipynb

import numpy as np
import math

genres = ['General Fiction', 'Romance', 'Fantasy', 'Science Fiction', 'Horror', 'Mystery', 'Young Adult']

# returns a list of readers that prefer the given genre
def preference(users, genre):
    return [user for user in users if user.preference_s[0] == genre]

# returns a dict that contains a list of readers by genre preference
def div_by_genre(users):
    users_by_genre = {}
    for genre in genres:
        users_by_genre[genre] = preference(users, genre)
    return users_by_genre

# returns the mean and standard deviation of the percentage of books read by each type of user
def calc_reading_preference(users_by_genre):
    reading_preference = []
    for genre in genres:    
        values = np.array([list(user.fiction_split_s.values()) for user in users_by_genre[genre]])
        reading_preference.append( (values.mean(axis=0), values.std(axis=0)) )
    return reading_preference

# Sort readers by the strength of their genre preference, and return those from the specified percentile
def div_genre_loyalists(users_by_genre, percentile):
    genre_loyalists = users_by_genre.copy()
    for genre in genres:
        u = users_by_genre[genre].copy()
        u.sort(key=lambda x: x.preference_s[1], reverse=True)
        genre_loyalists[genre] = u[:math.ceil(len(u)*percentile)]
    return genre_loyalists