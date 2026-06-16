#!/usr/bin/env python3
"""Simple search CLI for the wiki RAG index.

Usage:
    python3 search.py <query> [--kind wiki|raw_chat] [--top N]

Examples:
    python3 search.py "перспективы с Техинком"
    python3 search.py "кто такой Саша" --kind wiki --top 5
    python3 search.py "БИТ.Управление маркетплейсами" --top 10
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_index import search


def main():
    parser = argparse.ArgumentParser(description='Search the wiki RAG index')
    parser.add_argument('query', nargs='+', help='search query')
    parser.add_argument('--kind', choices=['wiki', 'raw_chat'], help='filter by kind')
    parser.add_argument('--top', type=int, default=5, help='number of results')
    parser.add_argument('--no-content', action='store_true', help='hide content preview')
    args = parser.parse_args()
    
    q = ' '.join(args.query)
    results = search(q, top_k=args.top, kind_filter=args.kind)
    
    print(f"Query: {q}")
    if args.kind:
        print(f"Filter: kind={args.kind}")
    print(f"Results: {len(results)}\n")
    
    for i, r in enumerate(results):
        print(f"--- Result {i+1} [score={r['score']:.3f}] [{r['kind']}] ---")
        print(f"Source: {r['source']}")
        print(f"Title: {r['title'][:80]}")
        if r.get('role'):
            print(f"Role: {r['role']}")
        if not args.no_content:
            print(f"Content (first 800):\n{r['content'][:800]}")
        print()


if __name__ == '__main__':
    main()
