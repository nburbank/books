#thesis 1: few authors dominate the lists (winner takes all)
#thesis 2: few publishers dominate the lists (oligarchy)
#pull data from the database
con = psycopg2.connect("dbname='nytimes'") 
cur = con.cursor()    
cur.execute("SELECT * FROM books")
rows = cur.fetchall()
con.close()
# import as a dataframe
data_frame = pd.DataFrame()
data_frame = pd.DataFrame(data = rows, columns=('id','title', 'isbn', 'author', 'list', 'rank', 'date', 'weeks on list', 'description', 'contributor', 'publisher', 'updated frequency' ) )
len(data_frame)

#subdivide the data for quicker iteration in practice 
test_length = len(data_frame)
test_data = data_frame.sample(test_length)
len(test_data)

best_filter = test_data['list'] == 'Combined Print & E-Book Fiction'
#test_data = test_data[best_filter]
print len(test_data)

# get the count by author
authors = test_data['author']
author_freq = authors.value_counts()
author_names = author_freq.keys()

# get the count by book
books = test_data['title']
book_freq = books.value_counts()
book_titles = book_freq.keys()

book_stats = pd.DataFrame(columns = ('title', 'score','author', 'author book count'))

counter = 0
for title in book_titles:
    filter_vector = (books == title)
    score = sum(6- test_data[filter_vector]['rank'])
    author = test_data[filter_vector]['author'].unique()[0]
    
    filter_vector = (authors == author)
    titles = test_data[filter_vector]['title']
    author_book_count = len(titles.unique())
    
    book_stats.loc[counter] = [title, score, author, author_book_count]
    counter += 1

print np.corrcoef(book_stats['score'], book_stats['author book count'])

import matplotlib.pyplot as plt
%matplotlib inline

one_hitters = book_stats[(book_stats['author book count'] == 1)] 
winners = book_stats[(book_stats['author book count'] > 1)] 

plt.hist(one_hitters['score'], bins = 150, color = 'blue', alpha = .5)

print np.mean(winners['score'])
print np.mean(one_hitters['score'])

plt.scatter(book_stats['author book count'], book_stats['score'], alpha = 0.5)
