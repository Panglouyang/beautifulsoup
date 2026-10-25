"""Print all tags: selecting every tag offers no pruning benefit."""
from _common import main
from bs4 import SoupStrainer

if __name__ == "__main__":
    main("Print every tag using SoupStrainer(True)", strainer=SoupStrainer(True))
