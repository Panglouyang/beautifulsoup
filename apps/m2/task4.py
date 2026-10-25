"""Print tags with an id, including an empty id, using SoupStrainer."""
from _common import main
from bs4 import SoupStrainer

if __name__ == "__main__":
    main("Print tags with an id attribute", strainer=SoupStrainer(id=True))
