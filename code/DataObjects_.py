# Contains classes used to read the Goodreads dataset
# Creates Book and User objects that contain functions to aid in analyzing data

import random
from operator import itemgetter
from collections import OrderedDict

class Book:

	# Paths to book data files
	fiction = 'C:/docs/GoodreadsDataAnalysis/data/fiction.txt'
	unlabeled = 'C:/docs/GoodreadsDataAnalysis/data/books_get_genre.txt'
	nonfiction = 'C:/docs/GoodreadsDataAnalysis/data/nonfiction.txt'
	no_genre = 'C:/docs/GoodreadsDataAnalysis/data/books_no_genre.txt'
	
	genres = ['Fiction', 'Romance', 'Fantasy', 'Science Fiction', 'Horror', 'Mystery', 'Suspense', 'Young Adult']

	def __init__(self, gr_id, title, author, pub_date, num_ratings, avg_rating, genre, id=0):
		self.id = id
		self.gr_id = int(gr_id)
		self.title = title
		self.author = author
		self.pub_date = pub_date
		self.num_ratings = num_ratings
		self.avg_rating = avg_rating
		self.genre = genre
		self.genre_estimate = ''
		self.genre_split = None
		self.fiction_split = None
		self.labels = None
		self.fiction_count = 0
		
	def __str__(self):
		return str(self.gr_id) + ' ' + self.title[:25] + ' by ' + self.author + ' ' + self.genre + ' ' + self.avg_rating

	# TODO pull nonfiction and no_genre
	def get_books(book_ids, labeled_fiction=True, unlabeled_books=True, nonfiction=False, no_genre=False):
		books = {}
		if unlabeled_books:
			f = open(Book.unlabeled, 'r', encoding='latin1')
			for line in f:
				arr = line.split('\t')
				books[arr[0]] = Book(arr[0], arr[1], arr[2], arr[3], arr[6], arr[7].strip(), 'none')
			f.close()
		if labeled_fiction:
			f = open(Book.fiction, 'r', encoding='latin1')
			for line in f:
				arr = line.split('\t')
				books[arr[0]] = Book(arr[0], arr[1], arr[2], arr[3], arr[6], arr[7], arr[9].strip())
			f.close()
		if len(book_ids) > 0:
			books = Utilities_.subset(books, book_ids)
		return books
		
	def save(books, file):
		f = open(file, 'a', encoding='latin1')
		for book in books:
			b = book
			f.write(str(b.gr_id) + '\t' + b.title + '\t' + b.author + '\t' + b.pub_date + '\t' + '' + '\t' + '' + '\t' + str(b.num_ratings) + '\t' + str(b.avg_rating) + '\n')
		f.close()
		

class User:

	ratings_file = 'C:/docs/GoodreadsDataAnalysis/data/book_titles/little_monsters/little_monsters_ratings_clean_.txt'   #core/ratings/ratings_test.txt'

	all_books = Book.get_books()

	def __init__(self, id, gr_id, books):
		self.id = id
		self.gr_id = int(gr_id)
		self.books = books # List of (book, rating) tuples
		self.avg_rating = self.get_avg_rating()
		self.genre_split = None
		self.genre_split_s = None
		self.fiction_split = None
		self.fiction_split_s = None
		self.labels = None
		self.labels_s = None
		self.preference = None
		self.preference_s = None
		
	def __eq__(self, other):
		return self.gr_id == other.gr_id
		
	def __str__(self):
		return str(self.id) + ': ' + str(self.gr_id) + ': ' + 'Rated ' + str(len(self.books)) + ' books'
								
	def get_users(file, users, sample=True): # Removed default argument
		include_all = len(users) == 0;
		ratings = User.get_ratings(file, users=users)
		users = []
		books = []
		
		for user_id, book_ids in ratings.items():
			for id in book_ids:
				if (id[1] in User.all_books):
					books.append((User.all_books[id[1]], id[2]))
			user = User(len(users), user_id, books)
			if sample:
				user.sample(145)
				user.analysis()
			users.append(user)
			books = []
		return users
		
	def load_users(user_file, ratings_file):
		users = []
		samples = []
		f = open(user_file, 'r')
		for line in f:
			sample = []
			line = line.strip()
			arr = line.split('\t')
			users.append(arr[0])
			a = arr[1:]
			for i in range(0, len(a), 2):
				if a[i] in User.all_books:
					sample.append( (User.all_books[a[i]], a[i+1]) )
			samples.append(sample)
			
		users = User.get_users(ratings_file, users, sample=False)
		for i in range(0, len(users)):
			users[i].samples = samples[i]
			users[i].analysis()
		return users
		
	def get_ratings(file, users):
		keys = set()
		values = []
		f = open(file, 'r')
		for line in f:
			arr = line.split('\t')
			keys.add(arr[0])
			values.append( (arr[0], arr[1], int(arr[2].strip())) )
		f.close()
		ratings = {key: [] for key in keys}
		for value in values:
			ratings[value[0]].append(value)
		if len(users) > 0:
			ratings = Utilities_.subset(ratings, users)
		return ratings

		
	# Returns a user_id list users who rated a book
	def get_users_by_book(file, book_ids, rating=''):
		no_rating = rating == ''
		books = {}
		users = []
		f = open(file, 'r')
		for line in f:
			arr = line.split('\t')
			if no_rating or arr[2].strip() == rating:
				if arr[1] in books:
					books[arr[1]].append(arr[0])
				else:
					books[arr[1]] = [arr[0]]
		
		for id in book_ids:
			if id in books:
				users = users + books[id]
		return User.get_users(file, users)
		
		
	def get_user_by_id(id, users):
		for user in users:
			if id == user.gr_id:
				return user
		return None
		
		
	def get_avg_rating(self):
		cum_rating = 0
		avg = 0
		for book, rating in self.books:
			cum_rating = cum_rating + rating
		if len(self.books) > 0:
			avg = cum_rating / len(self.books)
		return avg
		
			
	def genre(self):
		self.labels, self.genre_split = User.get_genre_split(self.books)
		self.labels_s, self.genre_split_s = User.get_genre_split(self.samples)
		

	def get_genre_split(books):
		labeled = 0
		unlabeled = 0
		genre_split = {'Fiction': 0, 'Romance': 0, 'Fantasy': 0, 'Science Fiction': 0, \
					   'Comics': 0, 'Horror': 0, 'Mystery': 0, 'Suspense': 0, \
					   'Young Adult': 0, 'Nonfiction': 0, 'none': 0	}
		for book in books: 
			if book[0] != None:
				genre = book[0].genre
				if genre == 'Womens Fiction':
					genre = 'Fiction'
				genre_split[genre] = genre_split[genre] + 1
				if genre == 'none':
					unlabeled = unlabeled + 1
				else:
					labeled = labeled + 1
		return ((labeled, unlabeled), genre_split)

		
	def get_fiction_split(genre_split):
		gs = genre_split
		tf = gs['Fiction'] + gs['Romance'] + gs['Fantasy'] + gs['Science Fiction'] + \
						gs['Horror'] + gs['Mystery'] + gs['Suspense'] + gs['Young Adult']
		if tf == 0: # Check for division by zero
			tf = 0.0000001
		fiction_split = OrderedDict([('Fiction', gs['Fiction'] / tf), ('Romance', gs['Romance'] / tf), \
						 ('Fantasy', gs['Fantasy'] / tf), ('Science Fiction', gs['Science Fiction'] / tf), \
						 ('Horror', gs['Horror'] / tf), ('Mystery', gs['Mystery'] / tf), ('Suspense', gs['Suspense'] / tf), \
						 ('Young Adult', gs['Young Adult'] / tf)])
						 				 
		return fiction_split
		
	def parse_fiction(self):
		self.genre()
		self.fiction_split = User.get_fiction_split(self.genre_split)
		self.fiction_split_s = User.get_fiction_split(self.genre_split_s)
		
	def get_preference(fiction_split):
		fiction = []
		for key, value in fiction_split.items():
			fiction.append( (key, value) )
		fiction.sort(key=itemgetter(1), reverse=True)
		preference = fiction[0][0]
		#margin = fiction[0][1] - fiction[1][1]		# Instead of using margin, have switched to using percentage
		return (preference, fiction_split[preference])
		self.preference = (preference, margin)	

	def analysis(self):
		self.parse_fiction()
		self.preference = User.get_preference(self.fiction_split)
		self.preference_s = User.get_preference(self.fiction_split_s)
		
	def display_data(self):
		labeled = self.labels[0]
		unlabeled = self.labels[1]
		p = 0
		if labeled + unlabeled > 0:
			p = labeled / (labeled + unlabeled)
		print('sample proportion: ' + str(p) + '; labeled = ' + str(labeled) + ' ; unlabeled = ' + str(unlabeled)) 
		
	def sample(self, k):
		books = []
		for book in self.books:
			books.append(book)
		if len(books) > k:
			self.samples = random.sample(books, k)
		else:
			self.samples = books
						
	def save_user(self, file):
		f = open(file, 'a')
		f.write(str(self.gr_id) + '\n')
		f.close()
		
	def save_sampled(self, user_file, get_genre_file):
		f = open(user_file, 'a')
		f.write(str(self.gr_id) + '\t')
		for sample in self.samples:
			f.write(str(sample[0].gr_id) + '\t' + str(sample[1]) + '\t')
		f.write('\n')
		f.close()
		
		f = open(get_genre_file, 'a', encoding='latin1')
		for sample in self.samples:
			if sample[0].genre == 'none':
				f.write(str(sample[0].gr_id) + '\t' + sample[0].title + '\t' + sample[0].author + '\t' + sample[0].pub_date + '\t' + '' + '\t' + '' + '\t' + str(sample[0].num_ratings) + '\t' + str(sample[0].avg_rating) + '\n')
		f.close()
	
	
#class UserBook:

#	def __init__(self, book, rating):
#		self.book = book
#		self.rating = rating
		
		
class DataHandler:

	def __init__(self):
		self.a = 10


	def get_users(ratings_file, books_file):
		users = []
		books = read_books(books_file)
		f = open(ratings_file, 'r')
		for line in f:
			arr = line.split('\t')
			
		
	def read_books(books_file):
		books = []
		f = open(books_file, 'r')
		for line in f:
			arr = line.split('\t')
			books.append(Book(arr[0], arr[1], arr[2], arr[3]))
		return books
		
	def book_by_id(books, id):
		for book in books:
			if book.gr_id == id:
				return book
		return None
		

class Utilities_:
		
	def subset(dictionary, ids):
		sub = {}
		for id in ids:
			if id in dictionary:
				sub[id] = dictionary[id]
		return sub
		
	def dict_to_list(dictionary):
		values = []
		for key, value in dictionary.items():
			values.append(value)
		return values
