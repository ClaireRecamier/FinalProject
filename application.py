import os
import wikipedia
import wikipediaapi


from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import apology, login_required, lookup, usd

#initialize english wikipedia object
wiki = wikipediaapi.Wikipedia('en')

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


#GLOBAL VARIABLES (instead of using a database)
#define relev_art as the list of relevant articles from the search(es)
relev_art = []
#define chosen_art as the list of chosen articles from the checkbox form on index.html.
chosen_art = []
#define chosen_sec as the list of chosen sections (format "Article:SectionTitle") from checkbox form on extract.html
chosen_sec = []
#define chosen_links as the list of chosen links from checkbox from on extractlinks.html
chosen_links = []


@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    if request.method == "POST":
        #define a variable called search that is the input of the search form
        search = request.form.get("Wikipedia Search")
        #goal is not to have repeated articles in main list, even if the page is reloaded and the same form is resubmitted
        #define a temporary list of relevant articles returned from the search
        temp_relev_art = wikipedia.search(search)
        #pare down temporary list to relevant articles not already in main list
        temp_relev_art = list(set(temp_relev_art).difference(relev_art))
        #add the items in temporary list to main list
        relev_art.extend(temp_relev_art)
        #send main updated list to html file to be posted
        return render_template("index.html",list_art=relev_art)

    else:
        #if homepage button is pressed or user exits and logs in again, clear the main list.
        relev_art.clear()
        return render_template("index.html")
#    return apology("Failed Search")


@app.route("/extractsections", methods=["GET", "POST"])
@login_required
def extractsections():
    if request.method == "POST":
        #get list of checked titles from form
        global chosen_art
        chosen_art.clear()
        chosen_art = request.form.getlist("art title")
        #print(chosen_art)
        #create list of sections
        sections = []
        for art in chosen_art:
            #print(art)
            #look up the article in the wiki object
            page = wiki.page(art)
            #extract the sections from each article. will set sec equal to a list of sections w all info
            sec = page.sections
            #define a list of titles of each section. initialize as empty
            titles = []
            for s in sec:
                #append the title of each section to titles list.
                titles.append(s.title)
            #adds the list of section titles for that article as an object inside the list "sections"
            sections.append(titles)
        #print(sections)
        return render_template("extract.html",chosen_art=chosen_art,sections=sections,len=len(chosen_art))
    else:
        #I don't think code actually ever gets here but in case it does, it hasn't obtained the chosen articles yet so display that again
        #print("HEREEEEEE")
        return render_template("index.html",list_art=relev_art)
    return apology("end")


@app.route("/extractlinks", methods=["GET", "POST"])
@login_required
def extractlinks():
    if request.method == "POST":
        # print("got here")-this printed so info is getting to post method for sure
        #update global variable with list of selectected sections from html form from extract.html
        global chosen_sec
        #update the global variable chosen_sec with the list of selected selections
        chosen_sec = request.form.getlist("sel_section")
        links = []
        #list of articles for which user wants all links
        art_link = []
        #bool to determine which pathway to take. if false, will go to "else" statement and send straight to double-check.
        path = False
        for art in chosen_art:
            #if the checkbox for "all links to other pages" for that article is clicked, then send to extractlinks.html
            #print(request.form.get(art + ":other_links")) <- this printed yes
            if request.form.get(art + ":other_links") == "yes":
                #change path to extractlinks.html if the user asks for all links to other pages to be displayed.
                path = True
                #add the article title to the list of articles for which user wants all links
                art_link.append(art)
                #get all info for that page
                page = wiki.page(art)
                #get all links for that page
                lin = page.links
                #append to links list an item which is the a list of all the titles of links in that article
                links.append(lin.keys())
        if path == True:
            return render_template("extractlinks.html",chosen_art=art_link,links=links,len=len(art_link))
        #if the checkbox for all links to other pages is not clicked, send straight to double-check
        else:
            #print("got here") <- this printed so it does get here
            #return render_template("check.html", chosen_art=chosen_art, chosen_sec=chosen_sec)
            return redirect(url_for('check'))
    else:
        return render_template("extract.html")
    return apology("even worse")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/check", methods=["GET", "POST"])
@login_required
def check():
    lengths = []
    for art in chosen_art:
        lengths.append(len(art))
    if request.method == "POST":
        global chosen_links
        chosen_links = request.form.getlist("sel_link")
        #print(chosen_art)
        #print(chosen_sec)
        #print(chosen_links)
        return render_template("check.html", chosen_art=chosen_art, chosen_sec=chosen_sec, chosen_links=chosen_links, lengths=lengths, len=len(lengths))
    else:
        #print("got here") <- if path variable in /extractlinks was set to false, redirects here.
        return render_template("check.html", chosen_art=chosen_art, chosen_sec=chosen_sec, chosen_links=chosen_links, lengths=lengths, len=len(lengths))
    return apology("annoyed")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    #if method = post, store and manipulate info from form
    if request.method == "POST":
        passwords_match = False
        username_exists = True
        username = request.form.get("username")
        password = request.form.get("password")
        secondpassword = request.form.get("confirmation")
        query = db.execute("SELECT username FROM users WHERE username=:name", name=username)
        if len(username) == 0 or len(password) == 0 or len(secondpassword) == 0:
            return apology("MUST not leave fields blank")
        if  len(query) == 0:
            username_exists = False
        else:
            return apology("username already exists")
        if password == secondpassword:
            passwords_match = True
            hash = generate_password_hash(password)
        else:
            return apology("passwords do not match")
#        if len(password) < 7:
#            return apology("password is too short")
        if username_exists == False and passwords_match == True:
            db.execute("INSERT INTO users (username,hash) VALUES(:username,:hash)",username=username,hash=hash)
            return render_template("login.html")
    return apology("TODO")


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    print(chosen_art)
    if request.method == "POST":
        f = open("WikiBook.txt","w+")
        articles = request.form.getlist("articles")
        sections = request.form.getlist("sections")
        links = request.form.getlist("links")
        #iterate through list of articles retrieved from form
        for art in articles:
            #write article title and newline
            f.write(art + "\n")
            #lookup that page
            page = wiki.page(art)
            #lookup that page's sections
            compsec = page.sections
            #iterate thru the retrieved list of sections from form
            for sec in sections:
                #if the current article matches the article of this section
                if art in sec:
                    #iterate thru list of sections for current article
                    for sect in compsec:
                        #if the title of the section matches the retreived section, write it to file
                        if sect.title in sec:
                            f.write(sect.title + "\n")
                            f.write(sect.text + "\n")
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
