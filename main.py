from flask import Flask, render_template, request, redirect, send_file
from file import save_to_file
from extractors.berlin import extract_berlin_jobs
from extractors.wework import scraper

app = Flask("JobScrapper")
db = {}


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/search")
def search():
    keyword = request.args.get("keyword")
    if keyword == None:
        return redirect("/")
    if keyword in db:
        jobs = db[keyword]
    else:
        #indeed = extract_indeed_jobs(keyword)
        wwr = scraper(keyword)
        berlin = extract_berlin_jobs(keyword)
        #jobs = indeed + wwr
        jobs = wwr
        db[keyword] = jobs
    return render_template("search.html", keyword=keyword, jobs=jobs)


@app.route("/export")
def export():
    keyword = request.args.get("keyword")
    if keyword == None:
        return redirect("/")
    if keyword not in db:
        return redirect(f"/search?keyword={keyword}")
    save_to_file(keyword, db[keyword])
    return send_file(f"{keyword}.csv", as_attachment=True)


app.run("0.0.0.0")
