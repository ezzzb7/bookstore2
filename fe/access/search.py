import requests
from urllib.parse import urljoin


class Search:
    def __init__(self, url_prefix):
        self.url_prefix = urljoin(url_prefix, "search/")

    def search_books(
        self, keyword: str, store_id: str = None, page: int = 1,
        page_size: int = 20, search_scope: str = "all"
    ) -> (int, list, int):
        """
        搜索图书
        :param keyword: 搜索关键字
        :param store_id: 商店ID，如果指定则只在该商店搜索
        :param page: 页码
        :param page_size: 每页大小
        :param search_scope: 搜索范围 - all, title, author, tags, content
        :return: (状态码, 图书列表, 总数)
        """
        json = {
            "keyword": keyword,
            "page": page,
            "page_size": page_size,
            "search_scope": search_scope,
        }
        if store_id:
            json["store_id"] = store_id
        
        url = urljoin(self.url_prefix, "books")
        r = requests.post(url, json=json)
        response_json = r.json()
        return r.status_code, response_json.get("books", []), response_json.get("total", 0)
