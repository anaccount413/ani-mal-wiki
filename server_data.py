""" database access
docs:
* http://initd.org/psycopg/docs/
* http://initd.org/psycopg/docs/pool.html
* http://initd.org/psycopg/docs/extras.html#dictionary-like-cursor
"""

from contextlib import contextmanager
import logging
import os
import json
from flask import current_app, g, json

import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import DictCursor

pool = None

def setup():
    global pool
    DATABASE_URL = os.environ['DATABASE_URL']
    current_app.logger.info(f"creating db connection pool")
    pool = ThreadedConnectionPool(1, 100, dsn=DATABASE_URL, sslmode='require')


@contextmanager
def get_db_connection():
    try:
        connection = pool.getconn()
        yield connection
    finally:
        pool.putconn(connection)


@contextmanager
def get_db_cursor(commit=False):
    with get_db_connection() as connection:
      cursor = connection.cursor(cursor_factory=DictCursor)
      # cursor = connection.cursor()
      try:
          yield cursor
          if commit:
              connection.commit()
      finally:
          cursor.close()


# currently using 
# get article contents for display
def get_article(article_name):
    with get_db_cursor(True) as cur:
        query = "select article_htmlcontent from articles where article_title = %s"
        cur.execute("select article_htmlcontent, header_image, article_id, image_file from articles where article_title = %s", (article_name,))
        x = cur.fetchall()
        return x

# gets the infobox image for an article
def get_image(id):
    with get_db_cursor(True) as cur:
        query = "select image_file from articles where article_id=%s"
        cur.execute("select image_file from articles where article_id=%s", (id,))
        x = cur.fetchall()
        return x[0][0]

# currently using 
# get article delta contents for editing
def get_article_delta(article_name):
    with get_db_cursor(True) as cur:
        query = "select article_deltacontent from articles where article_title = %s"
        cur.execute("select article_deltacontent from articles where article_title = %s", (article_name,))
        x = cur.fetchall()
        return x

# currently using 
# check if article in db
def check_article_indb(article_name):
    with get_db_cursor(True) as cur:
        query = "select exists (select article_id from articles where article_title=%s)"
        cur.execute("select exists (select article_id from articles where article_title=%s)", (article_name,))
        x = cur.fetchall()
        return x

# currently using 
# add new article to db
def new_article(article_title, article_deltacontent, article_htmlcontent, user_id, image, is_image):
    with get_db_cursor(True) as cur:

        # go through string backwards, see if there are underscores/spaces at the end and get rid of them
        for i in range(len(article_title) - 1, -1, -1):
            if(article_title[i] == '_'):
                article_title = article_title[0: i]
            else:
                break
        

        if(is_image):
            query = "insert into articles(article_title, article_deltacontent, article_htmlcontent, user_id, image_file, published) values(%s, %s, %s, %s, %s, %s, %s)"
            cur.execute("insert into articles(article_title, article_deltacontent, article_htmlcontent, user_id, header_image, image_file, published) values(%s, %s, %s, %s, %s, %s, %s)", (article_title, article_deltacontent, article_htmlcontent, user_id, is_image, image, True))
       
        else:
            query = "insert into articles(article_title, article_deltacontent, article_htmlcontent, user_id, header_image, published) values(%s, %s, %s, %s, %s, %s)"
            cur.execute("insert into articles(article_title, article_deltacontent, article_htmlcontent, user_id, header_image, published) values(%s, %s, %s, %s, %s, %s)", (article_title, article_deltacontent, article_htmlcontent, user_id, is_image, True))
        
        return 1

# currently using 
# update article (for editing path)
def update_article(article_title, article_deltacontent, article_htmlcontent, user_id, image, is_image):
    with get_db_cursor(True) as cur:

        # if they changed image, users cannot take images off of posts but they can change them
        if(is_image):
            query = "update articles set article_deltacontent=%s, article_htmlcontent=%s, image_file=%s where article_title=%s and user_id=%s"
            cur.execute("update articles set article_deltacontent=%s, article_htmlcontent=%s, image_file=%s, header_image=%s, published=%s where article_title=%s and user_id=%s", (article_deltacontent, article_htmlcontent, image, is_image, True, article_title, user_id))

        else:
            query = "update articles set article_deltacontent=%s, article_htmlcontent=%s where article_title=%s and user_id=%s"
            cur.execute("update articles set article_deltacontent=%s, article_htmlcontent=%s, published=%s where article_title=%s and user_id=%s", (article_deltacontent, article_htmlcontent, True, article_title, user_id))
        
        return 1


#THIS FUNCTION WILL SEARCH THE 'ALL ARTICLE' DATABASE FOR THE SEARCH WORD
def create_index_for_search():
    with get_db_cursor(True) as cur:
        cur.execute("CREATE INDEX articleContent ON articles USING GIN (to_tsvector('english', article_content))");
        cur.execute("CREATE INDEX articleContent ON articles USING GIN (to_tsvector('english', article_content))");
        return 1
                   
def get_searched_articles(search_word):
    with get_db_cursor(True) as cur:
        cur.execute("SELECT * FROM articles WHERE to_tsvector('english', article_htmlcontent) @@ plainto_tsquery('english', %s) OR to_tsvector('english', article_title) @@ plainto_tsquery('english', %s)", (search_word, search_word))        
        x = cur.fetchall()
        return x
    
#THIS FUNCTION WILL NEED TO BE MODIFY WITH THE USER'S ID SO THAT
#THE USER GETS THEIR ACTUAL ARTICLES THAT THEY PUBLISHED
def get_timestamp():
    with get_db_cursor(True) as cur:
        cur.execute("select * from articles")
        x = cur.fetchall()
        return x

        
# SAVES THE USER'S ARTICLE
# currently using
def save_article(article_items, userid):
    with get_db_cursor(True) as cur:
        article_title = article_items["title"]
        article_content = article_items["delta"]
        
        for i in range(len(article_title) - 1, -1, -1):
            if(article_title[i] == '_'):
                article_title = article_title[0: i]
            else:
                break
            
        cur.execute("insert into articles(article_title, article_deltacontent, user_id, header_image, image_file) values(%s, %s, %s, %s, %s)", (article_title, article_content, userid, article_items["imageBool"], article_items["image"]))
        
        return 1

        
# UPDATE THE USER'S SAVED ARTICLES
# currently using
def update_saved_article(article_items, userid):
    with get_db_cursor(True) as cur:
        article_title = article_items["title"]
        article_content = article_items["delta"]
        is_image = article_items["imageBool"]
        
        if(is_image):
            cur.execute("update articles set article_deltacontent=%s, image_file=%s, header_image=%s where article_title=%s and user_id=%s", (article_content, article_items["image"],article_items["imageBool"], article_title, userid))
        else:
            cur.execute("update articles set article_deltacontent=%s where article_title=%s and user_id=%s", (article_content, article_title, userid))
        return 1
    
# DELETES THE USER'S SAVED ARTICLE
def delete_saved_article(article_items, userid):
    with get_db_cursor(True) as cur:
        article_title = article_items["title"]
        cur.execute("delete from articles where article_title=%s and user_id=%s", (article_title, userid))
        return 1
        

# currently using 
def add_user(user_name, user_email):
    with get_db_cursor(True) as cur:
        query = "INSERT into users(username, email) VALUES(%s, %s)"
        cur.execute("INSERT into users(username, email) VALUES(%s, %s)", (user_name, user_email))
        return 1        

# currently using 
# will check if user has been registered before
# return true or false
def check_registered(user_email):
    with get_db_cursor(True) as cur:
        query = "SELECT EXISTS(SELECT 1 from users where user_email=%s)"
        cur.execute("SELECT EXISTS(SELECT 1 from users where email=%s)", (user_email,))
        x = cur.fetchall()
        return x
    
# currently using 
# will get titles of articles that a user has edited/done
def get_articles_user(email):
    with get_db_cursor(True) as cur:
        # selects the titles of the articles a user has published/edited based on their emails
        # uses the foreign key user id
        query = "SELECT articles.title FROM articles JOIN users ON articles.user_id = users.user_id WHERE users.email =%s"
        cur.execute("SELECT articles.article_title, articles.article_id FROM articles JOIN users ON articles.user_id = users.user_id WHERE users.email =%s", (email,))
        x = cur.fetchall()
        return x

# currently using 
def get_userid(email):
    with get_db_cursor(True) as cur:
        query = "SELECT user_id FROM users WHERE email=%s"
        cur.execute("SELECT user_id FROM users WHERE email=%s", (email,))
        x = cur.fetchall()
        return x


# check if person generated a certain article
# first get user id from the user table
# then get list of article titles from article table based on the id
# then, check if article title parameter in the list
def check_generated(userID, article_title):
    with get_db_cursor(True) as cur:
        query2 = "SELECT user_id from articles where article_title=%s"
        cur.execute(query2, (article_title,))
        result = cur.fetchall()
        found_id = result[0][0]
        they_generated = (found_id == userID)

        return they_generated

# check if article is published or just saved
def check_published(article_title):
    with get_db_cursor(True) as cur:
        query = "SELECT published FROM articles WHERE article_title=%s"
        cur.execute(query, (article_title,))
        return cur.fetchall()[0]

