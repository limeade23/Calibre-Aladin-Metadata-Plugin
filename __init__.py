from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import json, re

from calibre.ebooks.metadata.book.base import Metadata
from calibre.ebooks.metadata.sources.base import Option, Source


class Aladin(Source):

    name = "Aladin OpenAPI"
    description = "Downloads metadata and covers from Aladin Open API."
    author = "Limeade23 <https://github.com/limeade23>"
    version = (0, 0, 2)
    minimum_calibre_version = (6, 10, 0)

    ALADIN_ID: str = "aladin"
    API_URL: str = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"

    options = (
        Option('api_key', 'string', '',
        _('API Key'),
        _('발급받은 API 인증키를 입력하세요. 여기서 발급받을 수 있습니다. https://www.aladin.co.kr/ttb/wblog_manage.aspx')),
    )

    capabilities = frozenset(["identify", "cover"])
    touched_fields = frozenset(
        [
            "title",
            "authors",
            "identifier:" + ALADIN_ID,
            "identifier:isbn",
            "comments",
            "publisher",
            "pubdate",
            "languages",
            "tags",
            "rating",
        ]
    )

    def identify(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=30,
    ):
        if not self.prefs['api_key']:
            log.error('API 키를 먼저 입력해 주세요.')
            return

        search_keyword = title
        books = self._search(search_keyword)
        
        for book in books:
            metadata = self._to_metadata(book)
            
            if isinstance(metadata, Metadata):
                item_id = metadata.identifiers[self.ALADIN_ID]
                
                if metadata.isbn:
                    self.cache_isbn_to_identifier(metadata.isbn, item_id)
                
                if metadata.cover_url:
                    self.cache_identifier_to_cover_url(item_id, metadata.cover_url)
                self.clean_downloaded_metadata(metadata)
                result_queue.put(metadata)


    def _search(self, title: str = "", timeout: int = 30):
        params = {
            "ttbkey": self.prefs['api_key'],
            "Query": title,
            "QueryType": "Keyword",
            "MaxResults": 10,
            "start": 1,
            "SearchTarget": "All",
            "output": "js",
            "Version": 20131101,
            "OptResult": "subInfo",
            "Cover": "Big",
        }

        query_string = urlencode(params)
        url = f"{self.API_URL}?{query_string}"

        request = Request(
            url,
            method="GET",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )

        with urlopen(request, timeout=timeout) as response:
            body = response.read()
            if response.status != 200:
                raise Exception(f"failed to search: {body.decode()}")

        if body:
            results = json.loads(body).get("item", [])
            if len(results) > 0:
                return results
                
        return None


    def _to_metadata(self, data: dict) -> Metadata:
        authors_str = data.get("author", "")
        authors = [re.sub(r'\s*\([^)]*\)', '', author).strip() for author in authors_str.split(',')]

        metadata = Metadata(data.get("title", ""), authors)
        metadata.comments = data.get("description", "")
        identifiers = data.get("itemId")
        metadata.set_identifier(self.ALADIN_ID, str(identifiers))
        metadata.isbn = data.get("isbn13", "")
        metadata.tags = data.get("categoryName", "").split(">")
        metadata.rating = data.get("customerReviewRank")

        date_string = data.get("pubDate")
        formatted_date = datetime.strptime(date_string, "%Y-%m-%d")
        metadata.pubdate = formatted_date
        metadata.publisher = data.get("publisher", "")
        metadata.language = "kor"
        metadata.cover_url = data.get("cover", "")

        return metadata


    def get_cached_cover_url(self, identifiers):
        item = identifiers.get(self.ALADIN_ID, None)
        if item is None:
            isbn = identifiers.get('isbn', None)
            if isbn:
                item = self.cached_isbn_to_identifier(isbn)
        
        if item:
            return self.cached_identifier_to_cover_url(item)
            
        return None


    def download_cover(
        self,
        log,
        result_queue,
        abort,
        title=None,
        authors=None,
        identifiers={},
        timeout=30,
        get_best_cover=False,
    ):
        cover_url = self.get_cached_cover_url(identifiers)
        
        if cover_url:
            log.info(
                    "Trying to download cover from: %s",
                    cover_url.replace("cover200", "cover500"),
                )
            try:
                with urlopen(
                    cover_url.replace("cover200", "cover500"), timeout=timeout
                ) as response:
                    cover = response.read()
                    result_queue.put((self, cover))

            except Exception as e:
                log.exception("Failed to download cover from: %s", cover_url)
                log.info("Downloading cover from: %s", cover_url)
                try:
                    with urlopen(cover_url, timeout=timeout) as response:
                        cover = response.read()
                        result_queue.put((self, cover))
                except Exception as e:
                    log.info("Downloading cover from: %s", cover_url)
        else:
            log.info("No cover found")