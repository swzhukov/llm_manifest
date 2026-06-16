#!/usr/bin/env python3
"""Context retrieval for Mavis — given a query, return top relevant chunks formatted for LLM context.

This is the script Mavis calls when she needs context for answering a user's question.

Usage:
    python3 query.py "перспективы с Техинком" --top 5 --output context.md
    python3 query.py "кто такой Миша" --kind wiki --top 3
"""
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from build_index import search


def format_for_context(results, max_total=8000):
    """Format search results as a context block for LLM consumption."""
    parts = []
    parts.append(f"# Контекст из вики (RAG retrieval)\n")
    parts.append(f"_Запрос: см. ниже_\n")
    parts.append(f"_Время: {datetime.now().isoformat()}_\n")
    parts.append(f"_Найдено: {len(results)} релевантных фрагментов_\n\n")
    
    total = 0
    for i, r in enumerate(results, 1):
        header = f"## [{i}] {r['title'][:80]} (score: {r['score']:.3f})\n"
        meta = f"_source: {r['source']} | kind: {r['kind']}"
        if r.get('role'):
            meta += f" | role: {r['role']}"
        meta += "_\n\n"
        body = r['content'][:2000]
        block = header + meta + body + "\n\n---\n\n"
        if total + len(block) > max_total:
            break
        parts.append(block)
        total += len(block)
    
    return ''.join(parts)


def main():
    parser = argparse.ArgumentParser(description='Query wiki RAG and format as LLM context')
    parser.add_argument('query', nargs='+', help='search query')
    parser.add_argument('--top', type=int, default=8, help='number of results (default 8)')
    parser.add_argument('--kind', choices=['wiki', 'raw_chat'], help='filter by kind')
    parser.add_argument('--output', help='output file (default: stdout)')
    parser.add_argument('--max-chars', type=int, default=12000, help='max total chars')
    parser.add_argument('--format', choices=['context', 'json', 'brief'], default='context')
    args = parser.parse_args()
    
    q = ' '.join(args.query)
    
    # Get more results than requested, then filter in formatting
    results = search(q, top_k=args.top, kind_filter=args.kind)
    
    if args.format == 'context':
        output = format_for_context(results, max_total=args.max_chars)
    elif args.format == 'json':
        output = json.dumps({'query': q, 'results': results}, ensure_ascii=False, indent=2)
    elif args.format == 'brief':
        lines = [f"Query: {q}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] [{r['score']:.3f}] {r['source']} — {r['title'][:60]}")
        output = '\n'.join(lines)
    
    if args.output:
        Path(args.output).write_text(output, encoding='utf-8')
        print(f"Written to {args.output} ({len(output)} chars)", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
