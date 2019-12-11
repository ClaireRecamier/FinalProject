import os
import wikipedia
import wikipediaapi


from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, send_file
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash


from helpers import apology

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
#app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


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
def index():
    global chosen_art
    global chosen_sec
    global chosen_links
    global relev_art
    if request.method == "POST":
        #define a variable called search that is the input of the search form
        search = request.form.get("Wikipedia Search")
        #goal is not to have repeated articles in main list, even if the page is reloaded and the same form is resubmitted
        #define a temporary list of relevant articles returned from the search
        temprelev_art = wikipedia.search(search)
        #pare down temporary list to relevant articles not already in main list
        temprelev_art = list(set(temprelev_art).difference(relev_art))
        #add the items in temporary list to main list
        relev_art.extend(temprelev_art)
        #send main updated list to html file to be posted
        return render_template("index.html",list_art=relev_art)
    else:
        #if homepage button is pressed or user exits, clear the main list.
        chosen_art.clear()
        chosen_sec.clear()
        chosen_links.clear()
        relev_art.clear()
        return render_template("index.html")
#    return apology("Failed Search")


@app.route("/extractsections", methods=["GET", "POST"])
def extractsections():
    global chosen_art
    #create list of sections
    sections = []
    #case where extracting sections for the first time, not extracting sections from links
    if request.method == "POST":
        #get list of checked titles from form
        chosen_art.extend(request.form.getlist("art title"))
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
        print("HEREEEEEE")
        return render_template("index.html",list_art=relev_art)
    return apology("end")


@app.route("/extractlinks", methods=["GET", "POST"])
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


@app.route("/check", methods=["GET", "POST"])
def check():
    lengths = []
    for art in chosen_art:
        lengths.append(len(art))
    if request.method == "POST":
        #i dont think this ever gets called
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



@app.route("/create", methods=["GET", "POST"])
def create():
    #print(chosen_art)
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
            complink = page.links
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
            for link in links:
                #if the current article matches the article of this section
                if art in link:
                    #iterate thru list of sections for current article
                    for lin in complink:
                        #if the title of the section matches the retreived section, write it to file
                        if lin.key() in sec:
                            f.write(lin.key() + "\n")
                            f.write(sect.text + "\n")
            #write a newline in between articles
            f.write("\n")
    return render_template("created.html")

@app.route("/download")
def downloadFile ():
    global chosen_art
    global chosen_sec
    global chosen_links
    chosen_art.clear()
    chosen_sec.clear()
    chosen_links.clear()
    return send_file("WikiBook.txt", attachment_filename="WikiBook.txt")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
