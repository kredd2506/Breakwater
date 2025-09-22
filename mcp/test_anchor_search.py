#!/usr/bin/env python3
"""Test anchor search for A100 GPU"""

from cache.nrp_complete_anchor_db import search_complete_anchors

def test_a100_search():
    """Test search for A100 GPU"""
    query = "A100 GPU request special"

    print("Testing A100 GPU search:")
    print(f"Query: {query}")
    print("=" * 50)

    results = search_complete_anchors(query)

    for i, result in enumerate(results, 1):
        print(f"{i}. {result['url']}")
        print(f"   Page: {result['page']}")
        print(f"   Anchor: {result['anchor']}")
        print(f"   Relevance: {result['relevance']}")
        print()

if __name__ == "__main__":
    test_a100_search()