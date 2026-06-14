from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os
import subprocess

app = Flask(__name__)
CORS(app)

# ❗ VULNERABILITY 1: Hardcoded secret
ADMIN_TOKEN = "admin123"

# ❗ VULNERABILITY 2: Hardcoded DB password
DB_PASSWORD = "root123"

books = [
    {"id": 1, "title": "DevSecOps Handbook", "author": "Alice", "available": True},
    {"id": 2, "title": "Docker Deep Dive", "author": "Bob", "available": True}
]

borrowed = []

# ---------------- UI ----------------
@app.route('/')
def home():
    # UI enabled
    return render_template("index.html")


# ---------------- API INFO (leaks secrets) ----------------
@app.route('/api')
def api():
    return jsonify({
        "message": "Library DevSecOps API Running 🚀",
        "status": "active",
        "admin_token": ADMIN_TOKEN,     # ❗ exposed secret
        "db_password": DB_PASSWORD      # ❗ exposed secret
    })


# ---------------- GET BOOKS ----------------
@app.route('/books')
def get_books():
    return jsonify({"count": len(books), "data": books})


# ---------------- SEARCH (no sanitization) ----------------
@app.route('/search')
def search():
    q = request.args.get("q", "")

    # ❗ weak input handling
    result = []
    for b in books:
        if q.lower() in b["title"].lower():
            result.append(b)

    return jsonify({"query": q, "data": result})


# ---------------- ADD BOOK (no validation) ----------------
@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()

    # ❗ unsafe access (no validation)
    new_book = {
        "id": len(books) + 1,
        "title": data["title"],
        "author": data["author"],
        "available": True
    }

    books.append(new_book)
    return jsonify(new_book)


# ---------------- BORROW (no auth) ----------------
@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow(book_id):
    user = request.args.get("user")

    for b in books:
        if b["id"] == book_id and b["available"]:
            b["available"] = False
            borrowed.append({"book": b, "user": user})
            return jsonify({"message": "Book borrowed", "user": user})

    return jsonify({"error": "Not available"}), 400


# ---------------- RETURN ----------------
@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    for b in books:
        if b["id"] == book_id:
            b["available"] = True
    return jsonify({"message": "Book returned"})


# ---------------- DEBUG (CRITICAL LEAK) ----------------
@app.route('/debug')
def debug():
    return jsonify({
        "books": books,
        "borrowed": borrowed,
        "system": os.popen("uname -a").read()  # ❗ command exposure
    })


# ---------------- COMMAND INJECTION ----------------
@app.route('/ping')
def ping():
    host = request.args.get("host")

    # ❗ unsafe command execution
    return subprocess.getoutput("ping -c 1 " + host)


# ---------------- FILE READ (path traversal) ----------------
@app.route('/read')
def read_file():
    file = request.args.get("file")

    # ❗ no path validation
    with open(file, "r") as f:
        return f.read()


# ---------------- ADMIN (weak auth) ----------------
@app.route('/admin')
def admin():
    token = request.args.get("token")

    if token == ADMIN_TOKEN:
        return jsonify({"message": "Welcome Admin"})
    return jsonify({"error": "Unauthorized"}), 401


if __name__ == "__main__":
    # ❗ debug mode ON (bad practice)
    app.run(host="0.0.0.0", port=5000, debug=True)