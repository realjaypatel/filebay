# client = MongoClient("mongodb+srv://user:user@cluster0.u3fdtma.mongodb.net/droplink")  # change for Atlas
from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import datetime
import math

app = Flask(__name__)

# ---------------------------
# MongoDB Setup
# ---------------------------
client = MongoClient("mongodb+srv://user:user@cluster0.u3fdtma.mongodb.net/droplink")
db = client.linkshare

links = db.links
comments = db.comments
counters = db.counters

# ---------------------------
# Auto-increment ID
# ---------------------------
def next_id():
    doc = counters.find_one_and_update(
        {"_id": "linkid"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True
    )
    return doc["seq"]

# ---------------------------
# Homepage with Pagination + Search
# ---------------------------
@app.route("/")
def home():
    page = int(request.args.get("page", 1))
    q = request.args.get("q", "")

    per_page = 20
    skip = (page - 1) * per_page

    query = {}
    if q:
        query = {"title": {"$regex": q, "$options": "i"}}

    total = links.count_documents(query)
    total_pages = max(1, math.ceil(total / per_page))

    data = list(
        links.find(query)
        .sort("id", -1)
        .skip(skip)
        .limit(per_page)
    )

    return render_template("home.html",
                           links=data,
                           page=page,
                           total_pages=total_pages)

# ---------------------------
# Add Link Page
# ---------------------------
@app.route("/add", methods=["GET", "POST"])
def add_link():
    if request.method == "POST":
        title = request.form["title"]
        url = request.form["link"]
        size = request.form.get("size", "")
        category = request.form.get("category", "all")
        desc = request.form.get("desc", "")
        submitted_by = request.form.get("submitted_by", "Anonymous")

        # ---------------------------
        # NEW: TAGS (comma separated)
        # ---------------------------
        tags_raw = request.form.get("tags", "")
        tags = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]

        link_id = next_id()

        links.insert_one({
            "id": link_id,
            "title": title,
            "url": url,
            "size": size,
            "category": category,
            "desc": desc,
            "tags": tags,          # NEW FIELD
            "submitted_by": submitted_by,
            "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })

        return redirect(url_for("view_link", link_id=link_id))

    return render_template("add.html")

# ---------------------------
# View Link Page
# ---------------------------
@app.route("/<int:link_id>")
def view_link(link_id):
    link = links.find_one({"id": link_id})
    if not link:
        return redirect("/")

    link_comments = list(comments.find({"link_id": link_id}).sort("id", 1))

    return render_template("post.html",
                           link=link,
                           comments=link_comments)

# ---------------------------
# Add Comment
# ---------------------------
@app.post("/comment/<int:link_id>")
def add_comment(link_id):
    username = request.form.get("username", "Anonymous")
    content = request.form["content"]

    comments.insert_one({
        "link_id": link_id,
        "username": username,
        "content": content,
        "created_at": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    })

    return redirect(f"/{link_id}")

# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
