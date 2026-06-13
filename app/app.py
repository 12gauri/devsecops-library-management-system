from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ❗ VULNERABILITY 1: Hardcoded secret (detected by SAST tools)
ADMIN_TOKEN = "admin123"

books = [
    {"id": 1, "title": "DevSecOps Handbook", "author": "Alice", "available": True},
    {"id": 2, "title": "Docker Deep Dive", "author": "Bob", "available": True}
]

borrowed = []

# ---------------- HOME ----------------
@app.route('/')
def home():
    return jsonify({
        "message": "Library DevSecOps API Running 🚀",
        "version": "1.0",
        "status": "active",
        "admin_token": ADMIN_TOKEN  # ❗ exposed secret
    })

# ---------------- GET BOOKS ----------------
@app.route('/books', methods=['GET'])
def get_books():
    return jsonify({
        "count": len(books),
        "data": books
    })

# ---------------- SEARCH (vulnerable pattern) ----------------
@app.route('/search')
def search():
    q = request.args.get("q", "")

    # ❗ VULNERABILITY 2: Weak input handling (no sanitization)
    result = []
    for b in books:
        if q.lower() in b["title"].lower():
            result.append(b)

    return jsonify({
        "query": q,
        "count": len(result),
        "data": result
    })

# ---------------- ADD BOOK ----------------
@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()

    # ❗ VULNERABILITY 3: No validation
    new_book = {
        "id": len(books) + 1,
        "title": data["title"],   # unsafe access
        "author": data["author"],
        "available": True
    }

    books.append(new_book)

    return jsonify({
        "message": "Book added",
        "data": new_book
    })

# ---------------- BORROW BOOK ----------------
@app.route('/borrow/<int:book_id>', methods=['POST'])
def borrow(book_id):
    user = request.args.get("user")  # ❗ VULNERABILITY 4: no auth check

    for b in books:
        if b["id"] == book_id and b["available"]:
            b["available"] = False
            borrowed.append({"book": b, "user": user})

            return jsonify({
                "message": "Book borrowed",
                "book": b,
                "user": user
            })

    return jsonify({"error": "Book not available"}), 400

# ---------------- RETURN BOOK ----------------
@app.route('/return/<int:book_id>', methods=['POST'])
def return_book(book_id):
    for b in books:
        if b["id"] == book_id:
            b["available"] = True

    return jsonify({
        "message": "Book returned",
        "book_id": book_id
    })

# ---------------- LOGGING ISSUE ----------------
@app.route('/debug')
def debug():
    # ❗ VULNERABILITY 5: Debug info exposed
    return jsonify({
        "env": "development",
        "debug_mode": True,
        "all_books": books,
        "borrowed": borrowed
    })

# ---------------- FAKE AUTH CHECK ----------------
@app.route('/admin')
def admin():
    token = request.args.get("token")

    # ❗ weak authentication check
    if token == ADMIN_TOKEN:
        return jsonify({"message": "Welcome Admin"})
    else:
        return jsonify({"error": "Unauthorized"}), 401


if __name__ == "__main__":
    # ❗ VULNERABILITY 6: debug enabled (detected by scanners)
    app.run(host="0.0.0.0", port=5000, debug=True)