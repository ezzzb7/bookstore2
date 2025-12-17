from flask import Blueprint
from flask import request
from flask import jsonify
from be.model.search import Search

bp_search = Blueprint("search", __name__, url_prefix="/search")


@bp_search.route("/books", methods=["POST"])
def search_books():
    keyword: str = request.json.get("keyword", "")
    store_id: str = request.json.get("store_id", None)
    page: int = request.json.get("page", 1)
    page_size: int = request.json.get("page_size", 20)
    search_scope: str = request.json.get("search_scope", "all")
    
    s = Search()
    code, message, books, total = s.search_books(
        keyword, store_id, page, page_size, search_scope
    )
    
    return jsonify({
        "message": message,
        "books": books,
        "total": total,
        "page": page,
        "page_size": page_size
    }), code
