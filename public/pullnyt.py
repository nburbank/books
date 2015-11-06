from urllib2 import Request, urlopen, URLError
import json
import psycopg2
import datetime

def make_URI(date):
    key = 'ec4e2a5e373e93f850f9be6c420bb73a:2:73271883'
    prefix = 'http://api.nytimes.com/svc/books/v3/lists/'
    overview = 'overview.json?published_date=' + str(date)
    api_key_string = "&api-key="  + key
    URI = prefix + overview + api_key_string    
#    print URI
    return URI

#function that pulls the json file from the nytimes api
def pull_nytimes_data(URI):
    request = Request(URI)
    response = urlopen(request)
    parsed_response = json.loads(response.read())
#    print parsed_response
    return parsed_response

#request_date = datetime.date(2015,10,19)
#request_date = datetime.date(2015, 6, 15)
#request_date = datetime.date(2011, 8, 15)
request_date = datetime.date(2008, 4, 26)

request_count = 0
while request_count < 200: 
        
    print request_count
    print request_date
    request_date = request_date - datetime.timedelta(7)
    
    #start with a function that makes the URI call for a given isbn number
    overview_uri = make_URI(str(request_date))
    
    request_count = request_count + 1
    
    parsed_json = pull_nytimes_data(overview_uri)
 #   print parsed_json.keys()

    #parse out the date (since it chooses the list that is closed to the date that you submit)
    parsed_json = pull_nytimes_data(overview_uri)

    #go one layer into results
    overview_results = parsed_json['results']

    #get the date
    date = overview_results['bestsellers_date'].encode('ascii', 'ignore')

    #go one layer into lists
    overview_lists = overview_results['lists']

    #set up the list that's going to feed to the database 
    all_bestsellers_list = list()

    #go through each of the lists
    for bestseller_list in overview_lists:
        #extract the common information: list name and update frequency
        list_name = bestseller_list['display_name'].encode('ascii', 'ignore')
        update_frequency = bestseller_list['updated'].encode('ascii', 'ignore')

        #go through each book in each list
        counter = 0
        for book in bestseller_list['books']:
            #extract the book level information
            rank = book['rank']
            title = book['title'].encode('ascii', 'ignore')
            author = book['author'].encode('ascii', 'ignore')
            isbn = book['primary_isbn10'].encode('ascii', 'ignore')
            description = book['description'].encode('ascii', 'ignore')
            contributor = book['contributor'].encode('ascii', 'ignore')
            publisher = book['publisher'].encode('ascii', 'ignore')

            #put all of the book level information together
            entry = [title, isbn, author, list_name, rank, date, description, contributor, publisher, update_frequency ]        

            #add to the list of book attribute lists
            all_bestsellers_list.append(entry)
            counter = counter + 1

            

    con = None
    con = psycopg2.connect(database='nytimes') 
    cur = con.cursor()
    query = "INSERT INTO books (title, isbn_10, author, list, rank, date, description, contributor, publisher, update_frequency) \
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

    cur.executemany(query, all_bestsellers_list)
    con.commit()
    con.close()


