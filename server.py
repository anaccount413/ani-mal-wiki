from flask import Flask, request, render_template, url_for, jsonify, json, make_response, session, redirect, abort
import server_data
import requests
import os
from os import environ as env
from urllib.parse import quote_plus, urlencode
from authlib.integrations.flask_client import OAuth
import server_data
import json
from bs4 import BeautifulSoup
from functools import wraps
import magic # for getting mimetype of images https://github.com/ahupp/python-magic#readme

app = Flask(__name__, static_folder='static')
app.secret_key = env.get('FLASK_SECRET')


oauth = OAuth(app)

# needed since application context is accessed in setup method
def initialize_db():
    with app.app_context():
        server_data.setup()

# initialize connection pool
initialize_db()


# manually get userinfo with access token
def get_user_info(access_token, domain):

    # endpoint with info
    userinfo_endpoint = f'https://{domain}/userinfo'

    # set authorization header to access token
    headers = {'Authorization': f'Bearer {access_token}'}

    # get from the userinfo endpoint
    response = requests.get(userinfo_endpoint, headers=headers)

    # if input is correct user info is gotten
    if response.status_code == 200:
        user_info = response.json()
        return user_info
    
    # otherwise failure
    else:
        print('failed: ', response.text)
        return None
    
# get token from information taken
def exchange_code_for_tokens(auth_code, client_id, client_secret, redirect_uri, domain):
    # get the endpoint
    token_endpoint = f'https://{domain}/oauth/token'

    # data params
    data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'code': auth_code
    }

    # send post request
    response = requests.post(token_endpoint, data=data)

    # get the token if request went through
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        return access_token

    # failure
    else:
        print('failed: ', response.text)
        return None

def requires_auth(f):
  @wraps(f)
  # args and kwargs are meant to preserve the original arguments for the case when original function/behavior is used
  def decorated(*args, **kwargs):
    if 'user_info' not in session:
      # Redirect to login page
      return redirect('/login')
    return f(*args, **kwargs) #do the original behavior

  return decorated


# inverted version of above, checks if user is logged in and redirects them to home page if so
# will be used if signed in users try to go to login page 
def requires_notlogged(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_info' in session:
        # Redirect to home page
            return redirect('/')
        return f(*args, **kwargs) 

    return decorated


@app.route("/login")
@requires_notlogged
def login():
    app.secret_key = env.get('FLASK_SECRET')
    return render_template("sign.html", auth0_client_id="XLfzXnhzrdQpeahIcoirLJCfWCFkINy8", auth0_domain="dev-1v32pxckr0hjab75.us.auth0.com")

# oath method from class wouldn't work, replaced it with manually querying the oath token and userinfo endpoints
@app.route("/callback", methods=["GET", "POST"])
@requires_notlogged
def callback():
    app.secret_key = env.get('FLASK_SECRET')
    code = request.args.get('code')
    client_id=env.get("AUTH0_CLIENT_ID")
    client_secret=env.get("AUTH0_CLIENT_SECRET")
    redirect_uri=url_for("callback", _external=True)
    domain = env.get("AUTH0_DOMAIN")
    x = exchange_code_for_tokens(code, client_id, client_secret, redirect_uri, domain)
    y = get_user_info(x, domain)
    username = y['nickname']
    email = y['email']

    # the query returns a list of lists, but there is only one list with one boolean 
    in_db = server_data.check_registered(email)[0][0]
    session['user_info'] = y

    if(not in_db):
        server_data.add_user(username, email)
        
    return redirect("/")
@app.route("/logout")
@requires_auth
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("homepage", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )
# initialize_db()

# headers/generate page button will be changing based on when users are logged in/out
# done with parameters sent to jinja 

@app.route("/")
def homepage():
    search = False
    logged_in = False
    if 'user_info' in session:
        logged_in = True

    return render_template("homepage.html", logged=logged_in)


# account page
@app.route("/myaccount")
@requires_auth
def userAccount():
    logged_in = True
    allArticles = server_data.get_articles_user(session['user_info']['email'])
    username = session['user_info']['name']
    return render_template("accountpage.html", data=allArticles, logged=logged_in, searchbar=True, username=username)

#ALL OF QUILL JS ROUTE

#FUNCTION BELOW DISPLAYS THE EDITOR FOR A NEW ARTICLE

@app.route("/myaccount/edit")
@requires_auth
def editingNewArticle():
    return render_template("editingpage.html", searchbar=True, logged=True)


#FUNCTION BELOW DISPLAYS ARTICLES THAT HAS ALREADY BEEN PUBLISHED/SAVED    
@app.route("/myaccount/edit/<title>")
@requires_auth
def editingPreviousArticle(title):
    # get user id of person generating article, once again formatted as list of lists but only one element in there
    user_id = server_data.get_userid(session['user_info']['email'])[0][0]
    getSavedArticle = server_data.get_article_delta(title)
    if(not getSavedArticle):
        abort(404)

    # content that was in there pre-update
    prev_content = getSavedArticle[0][0]
    
    #this is just replace the word true to be an actual boolean true when
    #it is going to be read by the getContents() function. Mainly used for
    #bolds, italics, underlines, etc
    prev_content = prev_content.replace("true", '"true"')
    
    prev_content = json.loads(prev_content)['ops']
    

    made_article = server_data.check_generated(user_id, title)
    if(made_article == False):
        abort(404)

    else:
        return render_template("savedpage.html", response=prev_content, editing=True, article_title=title, searchbar=True, logged=True)



#FUNCTION BELOW DISPLAYS THE PUBLISHED ARTICLE
#currently using
@app.route("/save", methods=["POST", "GET"])
@requires_auth
def saveUserArticle():
        verify = server_data.check_registered(session['user_info'].get('email'))
        #CHECKS IF THE USER IS ACTUALLY VALID (DOUBLE CHECKING)
        if(verify):
                    
            articleTitle = request.form["title"]
            deltaObject = request.form["delta"]
            imagecontents = request.files.get('image_content')
            
            if(imagecontents != None):
                is_image = True
                imagefile = imagecontents.read()
            else:
                imagefile = None
                is_image = False
                        
            articleItems = {
                "title" : articleTitle,
                "delta" : deltaObject,
                "image" : imagefile,
                "imageBool" : is_image
            }
            #GETS THE USER_ID SO WE CAN MAKE THE SAVED ARTICLE ACTUALLY UNDER THE CORRECT USER
            userId = server_data.get_userid(session['user_info'].get('email'))
            server_data.save_article(articleItems, userId[0][0])
            
            return jsonify(200)

#currently using
@app.route("/update", methods=["POST", "GET"])
@requires_auth
def updateUserArticle():
        verify = server_data.check_registered(session['user_info'].get('email'))
        #CHECKS IF THE USER IS ACTUALLY VALID (DOUBLE CHECKING)
        if(verify):
                    
            articleTitle = request.form["title"]
            deltaObject = request.form["delta"]
            imagecontents = request.files.get('image_content')
            
            if(imagecontents != None):
                is_image = True
                imagefile = imagecontents.read()
            else:
                imagefile = None
                is_image = False
                        
            articleItems = {
                "title" : articleTitle,
                "delta" : deltaObject,
                "image" : imagefile,
                "imageBool" : is_image
            }
            #GETS THE USER_ID SO WE CAN UPDATE THE SAVED ARTICLE ACTUALLY UNDER THE CORRECT USER
            userId = server_data.get_userid(session['user_info'].get('email'))

            server_data.update_saved_article(articleItems, userId[0][0])
            
            return jsonify(200)
        
@app.route("/delete", methods=["DELETE", "GET"])
def deleteUserArticle():
        verify = server_data.check_registered(session['user_info'].get('email'))
        
        if(verify):
            results = request.json
            articleTitle = results["title"]
            articleItems = {
                "title" : articleTitle
            }
            userId = server_data.get_userid(session['user_info'].get('email'))

            response = server_data.delete_saved_article(articleItems, userId[0][0])
            
            if(response == 1):
                return jsonify(200, articleTitle)
            else:
                return jsonify(500)
            
            
#=========================================================================
@app.route("/search", methods=["GET"])
def searchResults():
    
    search = request.args.get("search")
    searchword = search
    articleData = server_data.get_searched_articles(search)
    search = True
    logged_in = False
    if 'user_info' in session:
        logged_in = True
    

    return render_template("searchpage.html", data=articleData, search=search, logged=logged_in, searchword=searchword)


@app.route("/article/<article_title>",  methods=["POST", "GET"])
def get_article(article_title):
    # will need to check if article is in database first and if the person is the one who generated it
    # then, will need to query the database with that title to get content

    # first check if post or get
    # for post to be possible, users need to have been logged in and on the generate article page with the rich text editor
    # if get, it just needs to display the article
    # common flow after hitting publish for an article will be for the js to send fetch request to the post 
    # to send information, then after information is sent it will redirect to the get request for the article

    if(request.method == "POST"):
        selected = server_data.check_article_indb(article_title)
        in_db = selected[0][0]

        if(not in_db):

            # get data that was sent in the format of a form
            # json would've been fine, but form is better for getting the image data
            title = request.form["title"]
            contents = request.form["delta"]
            htmlcontents = request.form['html_content']
            
            imagecontents = request.files.get('image_content')
           
            # get user id of person generating article, once again formatted as list of lists but only one element in there
            user_id = server_data.get_userid(session['user_info']['email'])[0][0]

            if(imagecontents != None):
                is_image = True
                imagefile = imagecontents.read()

            else:
                imagefile = None
                is_image = False
            
            # server side check for length
            if(len(title) > 30 or len(title) < 3):
                abort(404)

            

            # send query with gathered information
            server_data.new_article(title, contents, htmlcontents, user_id, imagefile, is_image)

            # now that the title and contents are set, send to database and redirect to get method
            return redirect(url_for('get_article', article_title=title))
        
        # if it's already in the db, first check if they are the ones who made it, if so update, otherwise don't allow
        # if they try when not allowed, it is enough to return 404
        # this is second check, first check is when they go to edit page itself

        else:

            if('user_info' not in session):
                abort(404)

            user_id = server_data.get_userid(session['user_info']['email'])[0][0]

            made_article = server_data.check_generated(user_id, article_title)
    
            if(made_article == False):
                abort(404)
            
            title = request.form["title"]
            contents = request.form["delta"]
            htmlcontents = request.form['html_content']
            imagecontents = request.files.get('image_content')
        
           
            user_id = server_data.get_userid(session['user_info']['email'])[0][0]

            if(imagecontents != None):
                is_image = True
                imagefile = imagecontents.read()

            else:
                imagefile = None
                is_image = False


            # send query with gathered information
            server_data.update_article(title, contents, htmlcontents, user_id, imagefile, is_image)
            return "Success edit"

    else:
        # process the data being sent and give it to the template for dynamic generation
        # most processing is with the article contents, changing it from ops to some more readable form
        # will send content in the form of a list of dictionaries, with section header and section content
        # headers force newlines, so headers will always be paired with the nearest content after it

        selected = server_data.check_article_indb(article_title)
        in_db = selected[0][0]

        if(not in_db):
            abort(404)

        else:

            published = server_data.check_published(article_title)
            
            # if not published, file is not available as an article yet!
            if(published[0] == False):
                abort(404)

            all_data = server_data.get_article(article_title)[0]

            data = all_data[0]
        
            soup = BeautifulSoup(data, 'html.parser')

            h2_items = soup.find_all('h2')
           

            # loop through the h2s and assign an id to each of them
            # putting them in a list which will get iterated through when template is rendered
            count = 1
            heading_ids = []
            heading_contents = []

            for h2 in h2_items:
                heading_contents.append(h2.text)
                heading_ids.append("section" + str(count))
                h2['id'] = "section" + str(count)

                count += 1

            # now replace data with the new html that has ids for the headings
            data = soup.prettify()
            
            combined_data = zip(heading_ids, heading_contents)

            # for images, check if there is an infobox image in the article, if so add the image when rendering infobox
            # it will send a request to the image route
            is_image = all_data[1]
            article_id = all_data[2]


            if 'user_info' in session:
                logged_in = True
                user_id = server_data.get_userid(session['user_info']['email'])[0][0]
                made_article = server_data.check_generated(user_id, article_title)
            
            else:
                made_article = False
                logged_in = False
            
            

            return render_template("article.html", generated_article=made_article, logged=logged_in, title=article_title, contents=data,  heading_data = combined_data, present_image=is_image, articleID=article_id, searchbar = True)



@app.errorhandler(404)
def not_found(error):
    logged_in = False
    if('user_info' in session):
        logged_in = True
    return render_template('404.html', searchbar = True, logged=logged_in), 404

@app.route('/images/image<int:image_id>')
def get_image(image_id):

    # get the image from the database
    image_row = server_data.get_image(image_id)

    # get type of image (png, jpeg, etc.)
    mimer = magic.Magic(mime=True)
    image_bytes = bytes(image_row)
    the_type = mimer.from_buffer(image_bytes)

    # generate response
    the_response = make_response(image_bytes)
    the_response.headers['Content-Type'] = the_type

    # return image
    return the_response
   

if __name__ == "__main__":
    app.run(port=4131)