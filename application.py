import os
import wikipedia
import wikipediaapi


from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
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


#GLOBAL VARIABLES
#define relev_art as the list of relevant articles from the search(es)
relev_art = []
#define chosen_art as the list of chosen articles from the checkbox form on index.html
chosen_art = []
#define chosen_sec as the list of chosen sections (format "Article:SectionTitle") from checkbox form on extract.html
chosen_sec = []


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
        chosen_art = request.form.getlist("art title")
        #print(chosen_art)
        for art in chosen_art:
            #look up the article in the wikipedia object
            page = wiki.page('art')
            #extract the sections from each article. Getting the title of each article will b done in the jinja template w section.title
            sections = page.sections
        print(chosen_art)
        return render_template("extract.html",chosen_art=chosen_art,sections=sections)
    else:
        #I don't think code actually ever gets here but in case it does, it hasn't obtained the chosen articles yet so display that again
        #print("HEREEEEEE")
        return render_template("index.html",list_art=relev_art)
    return apology("end")


@app.route("/extractmore", methods=["GET", "POST"])
@login_required
def extractmore():
    if request.method == "POST":
        # print("got here")-this printed so info is getting to post method for sure
        #chosen_sec = request.form.getlist("sel_section")-successfully got the list of selected selections
        for art in chosen_art:
            page = wiki.page('art')
            links = page.links
            #return the list of titles (links.keys()), not the list of everything in each link
        return render_template("extractmore.html",chosen_art=chosen_art,links=links.keys())
    else:
        return render_template("extract.html")
    return apology("TODO")


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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    return apology("TODO")


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


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    return apology("TODO")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
