"""Day 10: sentimen berita berbasis leksikon (ID + EN), tanpa LLM.

Ini NADA berita secara umum, bukan dampak ke emiten: "royalti batu bara naik" bernada positif di sini
tapi negatif untuk penambang. Dampak per perusahaan = event_impacts (Day 11), bukan kolom ini.
Negasi sederhana: kata pembalik tepat sebelum kata kunci membalik tandanya.
"""
import re

from .. import db

POS = set("""naik menaik melonjak menguat meroket melesat untung laba rekor tumbuh ekspansi dividen positif kuat
surge surges surged rise rises rose rising gain gains gained profit profits record growth beat beats upgrade
rally rallies soar soars soared jump jumps jumped strong""".split())
NEG = set("""turun anjlok melemah rugi merosot jatuh gagal korupsi sanksi denda negatif krisis lemah
fall falls fell drop drops dropped plunge plunges plunged loss losses slump decline declines declined
downgrade probe lawsuit default fraud weak crash""".split())
NEGATORS = {"tidak", "tak", "belum", "bukan", "not", "no", "never"}


def score(title: str) -> str:
    words = re.findall(r"\w+", title.lower())
    total = 0
    for i, w in enumerate(words):
        sign = (w in POS) - (w in NEG)
        if sign and i and words[i - 1] in NEGATORS:
            sign = -sign
        total += sign
    return "POSITIVE" if total > 0 else "NEGATIVE" if total < 0 else "NEUTRAL"


def run() -> int:
    """Beri label pada berita yang belum bersentimen; idempoten. Return jumlah baris diisi."""
    with db.connect() as con:
        rows = con.execute("SELECT id, title FROM news WHERE sentiment IS NULL").fetchall()
        for r in rows:
            con.execute("UPDATE news SET sentiment=? WHERE id=?", (score(r["title"]), r["id"]))
    return len(rows)


if __name__ == "__main__":
    print(run())
