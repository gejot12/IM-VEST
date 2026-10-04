"""Satu perintah memperbarui semua data: `uv run python -m app.refresh [--quick]`.
--quick: lewati fundamental (lambat). Setiap langkah gagal-aman; hasil dicetak."""
import sys

from . import seed
from .ingest import gnews, yahoo
from .nlp import events, rules, sentiment


def main(quick: bool = False) -> None:
    seed.run()
    print("quotes:", yahoo.quotes())
    print("prices:", sum(yahoo.prices().values()), "bars")
    if not quick:
        r = yahoo.fundamentals()
        print("fundamentals:", sum(r.values()), "/", len(r))
    print("news baru:", gnews.run())
    print("tautan entitas:", rules.run(), "| sentimen:", sentiment.run(), "| event baru:", events.run())


if __name__ == "__main__":
    main("--quick" in sys.argv)
