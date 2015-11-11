
# coding: utf-8

# In[3]:

import json
import bottlenose
import xmltodict
from urllib2 import HTTPError
import time


# In[ ]:




# In[4]:

# make it into a dictionary for ease of use
authentication_dict = dict()
authentication_dict['username'] = str(authentication_list[0])
authentication_dict['id'] = str(authentication_list[1])
authentication_dict['key'] = str(authentication_list[2])
authentication_dict['associate'] = str(authentication_list[3])

# set up bottlenose to query amazon
amazon = bottlenose.Amazon(authentication_dict['id'], authentication_dict['key'], authentication_dict['associate'])


# In[ ]:




# In[5]:

# fetch data from the database that's going to be enhanced

import psycopg2
import pandas as pd

#pull data from the database
con = psycopg2.connect("dbname='nytimes'") 
cur = con.cursor()    
cur.execute("SELECT * FROM books")
rows = cur.fetchall()
con.close()

# import as a dataframe
data_frame = pd.DataFrame()
data_frame = pd.DataFrame(data = rows, columns=('id','title', 'isbn', 'author', 'list', 'rank', 'date', 'weeks on list', 'description', 'contributor', 'publisher', 'updated frequency' ) )

#partition data into a smaller set for trouble shooting and the such
title_list = data_frame['title'][1:1000]
isbn_list = data_frame['isbn'][1:1000]

isbn_title_dict = dict(zip(isbn_list,title_list))


# In[6]:

# search by isbn function
def search_by_isbn(isbn):
    if isbn == 'None':
        return 'no isbn'
    response = amazon.ItemLookup(IdType = "ISBN", ItemId=isbn, SearchIndex = "Books", ResponseGroup='Large')
    obj1 = xmltodict.parse(response)
    if 'Item' in obj1['ItemLookupResponse']['Items'].keys():
        if type(obj1['ItemLookupResponse']['Items']['Item']) == list:
            return obj1['ItemLookupResponse']['Items']['Item'][0]['ASIN']
        else:
            return obj1['ItemLookupResponse']['Items']['Item']['ASIN']
    else: #this happens with the isbn doens't get a response, becuase it's probably wrong
        return 'isbn to asin failure'

    
    
    
    
# first pass, try to get as many ASIN for ISBN out of the list
isbn_to_asin = dict()

# run through the isbn list from the database
for isbn in isbn_list:
    isbn_to_asin[isbn] = search_by_isbn(isbn)
    print isbn_to_asin[isbn]
    # pause to avoid 503 errors
    time.sleep(1)

# calculate the success rate
success_count = 0
for value in isbn_to_asin.values():
    if value != 'isbn to asin failure':
        if value != 'no isbn':
            success_count += 1
print
print (success_count+0.0)/len(isbn_to_asin)


# In[7]:

# make a list of the titles of the failed books, try to get ASIN using a title match
covered_books = dict()
uncovered_books = list()
for key in isbn_to_asin:
    if isbn_to_asin[key] == 'isbn to asin failure':
        uncovered_books.append(isbn_title_dict[key])
    elif isbn_to_asin[key] == 'no isbn':
        uncovered_books.append(isbn_title_dict[key])
    else:
        covered_books[isbn_title_dict[key]]= isbn_to_asin[key]
len(uncovered_books)


# In[11]:

import re


# search by title to produce potential matches
def search_by_title(title):
    # construct the query
    response=amazon.ItemSearch(Keywords=title, SearchIndex="Books")
    # parse xml
    obj2 = xmltodict.parse(response)
    # construct a dictionary of title:ASIN from that author
    title_asin_dict = dict()
    for object in obj2['ItemSearchResponse']['Items']['Item']:
        title_asin_dict[object['ItemAttributes']['Title']] = object['ASIN']    
    return title_asin_dict


# In[13]:

uncovered_title_asin_dict = dict()
inferred_asin_dict = dict()

for ex_title in uncovered_books:
    time.sleep(2)
    
    # step 1: get the potential matches
    potential_titles = search_by_title(ex_title)

    # step 2: identify matches with title as subset
    filtered_matches = dict()
    for title in potential_titles:
        if re.search(ex_title.lower(),title.lower()) != None:
            filtered_matches[title] = potential_titles[title]

    if len(filtered_matches) == 0:
        uncovered_title_asin_dict[ex_title] = 'no match'
#        print "no matches for " + str(ex_title)
#        print
        continue
    else:
        print ex_title
            
    # step 3: identify most frequent ASIN
    time.sleep(2)
    
    asin_rank_dict = dict()
    for filtered_match in filtered_matches:
        match_asin = filtered_matches[filtered_match]
        response=amazon.ItemLookup(ItemId=match_asin, ResponseGroup='Large')
        # parse xml
        obj2 = xmltodict.parse(response)
        
        if 'SalesRank' in obj2['ItemLookupResponse']['Items']['Item']:
            sales_rank = int(obj2['ItemLookupResponse']['Items']['Item']['SalesRank'])
            book_asin = obj2['ItemLookupResponse']['Items']['Item']['ASIN']        
            asin_rank_dict[sales_rank] = book_asin
        else:
            print "no sales rank found"   

    uncovered_title_asin_dict[ex_title] = asin_rank_dict
    
    # step 4: find the best ranked book
    
    best_rank = min(set(asin_rank_dict.keys()))
    print best_rank
    print len(asin_rank_dict)
    
    inferred_asin = asin_rank_dict[best_rank]
    print inferred_asin
    inferred_asin_dict[ex_title] = inferred_asin
    


# In[14]:

# combine collected and inferred asin's
z = covered_books.copy()
z.update(inferred_asin_dict)


# In[72]:

# function to take a response and extract author, title, description, nodelist, and isbn
def parse_xml(query_response): 
    # parse response
    obj3 = xmltodict.parse(query_response)
    # get the title
    
    if 'Author' in obj3['ItemLookupResponse']['Items']['Item']['ItemAttributes'].keys():
        print "ok zone"
        author = obj3['ItemLookupResponse']['Items']['Item']['ItemAttributes']['Author']
        title = obj3['ItemLookupResponse']['Items']['Item']['ItemAttributes']['Title']    
        description =  obj3['ItemLookupResponse']['Items']['Item']['EditorialReviews']
        

        if type(description['EditorialReview']) == list:
            description = description['EditorialReview'][0]['Content']
        else:
            description = description['EditorialReview']['Content']
        

        # pull out the list of 
        node_list = list()
        for node in obj3['ItemLookupResponse']['Items']['Item']['BrowseNodes']['BrowseNode']:

            if type(node) == list:
                node_list.append([node[0]['BrowseNodeId'], node[0]['Name']])    
            elif type(node) == unicode:
                print node
            else:
                node_list.append( [node['BrowseNodeId'], node['Name']] )    

            
            
            
            
        # pull the isbn number as well
        isbn =  obj3['ItemLookupResponse']['Items']['Item']['ItemAttributes']['ISBN']
        return [title, author, description, node_list, isbn]
    else:
        print 'not ok zone'
        

# go over the covered books and extract their data for the data fram

df = pd.DataFrame(columns = ['title', 'author', 'description', 'nodelist', 'isbn'])
values_list = list()

counter = 0
for book in z: 
    time.sleep(1)
    title = book
    asin = z[book]
    search = amazon.ItemLookup(ItemId=asin, ResponseGroup='Large')
    print title
    print counter
    values = parse_xml(search)
    
    df.loc[counter] = values
    values_list.append(values)
    
    counter += 1
    


# In[73]:

def put_in_database(results_as_a_list):    
    con = None
    con = psycopg2.connect(database='nytimes') 
    cur = con.cursor()
    query = "INSERT INTO amazon (title, author, description, nodelist, isbn) VALUES (%s, %s, %s, %s, %s)"
    cur.executemany(query, results_as_a_list)
    con.commit()
    con.close()
    return


put_in_database(values_list)


# In[70]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[76]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:



