"""Berita dari Google News RSS (tanpa key). Feed ini diizinkan Google untuk pembaca feed pribadi, NON-komersial:
cukup untuk prototipe; produksi wajib provider berita berlisensi. Hanya menyimpan judul + tautan + penerbit.
"""
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

from .. import db
from ..nlp.rules import short_name

SOURCE = ("Google News RSS", "Google", "THIRD_PARTY")
TOPICS = ["harga nikel", "harga batu bara", "royalti batu bara", "harga CPO sawit", "harga emas", "harga minyak mentah",
          "IHSG saham", "kebijakan hilirisasi nikel", "harga tembaga", "gempa tambang Indonesia"]


def fetch(query: str, when: str = "7d") -> list[dict]:
    qs = urllib.parse.urlencode({"q": f"{query} when:{when}", "hl": "id", "gl": "ID", "ceid": "ID:id"})
    req = urllib.request.Request(f"https://news.google.com/rss/search?{qs}", headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return parse(r.read())


def parse(xml: bytes) -> list[dict]:
    out = []
    for it in ET.fromstring(xml).iter("item"):
        publisher = (it.findtext("source") or "").strip()
        title = re.sub(rf"\s+-\s+{re.escape(publisher)}$", "", it.findtext("title", "").strip()) if publisher else it.findtext("title", "").strip()
        out.append({"title": title, "url": it.findtext("link"), "publisher": publisher or None,
                    "published_at": parsedate_to_datetime(it.findtext("pubDate")).astimezone().replace(tzinfo=None).isoformat(timespec="seconds")})
    return out


def store(con, articles: list[dict], source_id: int) -> int:
    return sum(con.execute("INSERT OR IGNORE INTO news(title, url, publisher, published_at, source_id) VALUES (?,?,?,?,?)",
                           (a["title"], a["url"], a["publisher"], a["published_at"], source_id)).rowcount for a in articles)


def run(fetcher=fetch, delay: float = 1.0, limit_per_query: int = 15) -> int:
    added = 0
    with db.connect() as con:
        con.execute("INSERT OR IGNORE INTO data_sources(name, provider, source_type) VALUES (?,?,?)", SOURCE)
        src = con.execute("SELECT id FROM data_sources WHERE name=?", (SOURCE[0],)).fetchone()["id"]
        queries = TOPICS + [f'"{short_name(r["name"])}"' for r in con.execute("SELECT name FROM companies")]
        for i, q in enumerate(queries):
            if i:
                time.sleep(delay)
            try:
                added += store(con, fetcher(q)[:limit_per_query], src)
            except Exception as e:
                print(f"skip {q!r}: {e}")
    return added


if __name__ == "__main__":
    print(run())
