"""Print all anchors using SoupStrainer during parsing."""
from _common import main
from bs4 import SoupStrainer

if __name__ == "__main__":
    main("Print all a tags, including anchors without href", strainer=SoupStrainer("a"))
