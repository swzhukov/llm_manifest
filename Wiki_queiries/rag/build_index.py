#!/usr/bin/env python3
"""Build RAG index over wiki content + raw chats.

Uses TF-IDF with Russian-aware tokenization (manual pre-tokenization for bigrams).
"""

import os
import re
import json
import pickle
import sys
from pathlib import Path
from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

WIKI_DIR = Path('/workspace/wiki')
RAG_DIR = WIKI_DIR / 'rag'
INDEX_FILE = RAG_DIR / 'index.pkl'
CHUNKS_FILE = RAG_DIR / 'chunks.json'
VOCAB_FILE = RAG_DIR / 'vocab.pkl'

# === Russian-aware tokenization ===
WORD_RE = re.compile(r'[a-zа-яё0-9]+')

def tokenize(text):
    """Lowercase + word + bigram extraction for Russian."""
    words = WORD_RE.findall(text.lower())
    bigrams = [f"{w1}_{w2}" for w1, w2 in zip(words, words[1:])]
    return words + bigrams

# === Collect documents ===
def collect_documents():
    chunks = []
    chunk_id = 0
    
    # Wiki structured files
    for md_file in sorted(WIKI_DIR.rglob('*.md')):
        if 'raw_imports' in str(md_file):
            continue
        if '/rag/' in str(md_file):
            continue
        if md_file.name == 'INDEX.md':
            continue
        
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        
        # Split by ## sections
        sections = re.split(r'\n## ', content)
        for i, section in enumerate(sections):
            section = section.strip()
            if not section or len(section) < 50:
                continue
            lines = section.split('\n', 1)
            title = lines[0].strip().lstrip('#').strip()
            chunks.append({
                'id': chunk_id,
                'source': str(md_file.relative_to(WIKI_DIR)),
                'kind': 'wiki',
                'title': title[:200],
                'content': section[:5000],
            })
            chunk_id += 1
    
    # Raw chats
    raw_dir = RAG_DIR / 'full_chats'
    if raw_dir.exists():
        for md_file in sorted(raw_dir.glob('*.md')):
            try:
                content = md_file.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            
            sections = re.split(r'\n---\n\n', content)
            for section in sections:
                section = section.strip()
                if not section or len(section) < 50:
                    continue
                if section.startswith('# ') and len(section) < 200:
                    continue
                
                role = '?'
                if '## USER' in section:
                    role = 'USER'
                elif '## AI' in section:
                    role = 'AI'
                
                chunks.append({
                    'id': chunk_id,
                    'source': str(md_file.relative_to(WIKI_DIR)),
                    'kind': 'raw_chat',
                    'role': role,
                    'title': md_file.name.replace('.md', '')[:200],
                    'content': section[:3000],
                })
                chunk_id += 1
    
    return chunks

# === Build TF-IDF (manually for bigram support) ===
def build_index(chunks):
    documents = [c['content'] for c in chunks]
    
    # Build vocabulary
    print("Tokenizing all documents...")
    tokenized_docs = [tokenize(d) for d in documents]
    
    # Document frequency
    df = Counter()
    for tokens in tokenized_docs:
        df.update(set(tokens))
    
    # Filter: keep tokens that appear in >=2 docs and <= 95% of docs
    n_docs = len(documents)
    vocab = {}
    i = 0
    for tok, count in df.items():
        if count >= 2 and count <= 0.95 * n_docs:
            vocab[tok] = i
            i += 1
    print(f"Vocabulary: {len(vocab)} tokens")
    
    # Build sparse TF-IDF matrix
    from scipy.sparse import csr_matrix, lil_matrix
    import math
    
    rows, cols, data = [], [], []
    for doc_idx, tokens in enumerate(tokenized_docs):
        tf = Counter(tokens)
        if not tf:
            continue
        # Normalize TF
        n = sum(tf.values())
        for tok, count in tf.items():
            if tok not in vocab:
                continue
            col = vocab[tok]
            tf_val = count / n
            idf_val = math.log(n_docs / df[tok])
            rows.append(doc_idx)
            cols.append(col)
            data.append(tf_val * idf_val)
    
    n_features = len(vocab)
    tfidf_matrix = csr_matrix((data, (rows, cols)), shape=(n_docs, n_features))
    print(f"Matrix shape: {tfidf_matrix.shape}")
    print(f"Non-zeros: {tfidf_matrix.nnz}")
    
    return vocab, tfidf_matrix

# === Save ===
def save(vocab, tfidf_matrix, chunks):
    with open(VOCAB_FILE, 'wb') as f:
        pickle.dump(vocab, f)
    with open(INDEX_FILE, 'wb') as f:
        pickle.dump(tfidf_matrix, f)
    with open(CHUNKS_FILE, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False)
    
    # Compute norms for cosine similarity
    from scipy.sparse import vstack
    norms = np.sqrt(np.array(tfidf_matrix.multiply(tfidf_matrix).sum(axis=1)).flatten())
    norms[norms == 0] = 1.0
    np.save(RAG_DIR / 'norms.npy', norms)
    print("Saved.")

# === Search ===
_search_cache = {}

def search(query, top_k=5, kind_filter=None):
    """Search the index for a query."""
    if 'vocab' not in _search_cache:
        with open(VOCAB_FILE, 'rb') as f:
            vocab = pickle.load(f)
        with open(INDEX_FILE, 'rb') as f:
            tfidf_matrix = pickle.load(f)
        with open(CHUNKS_FILE, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        norms = np.load(RAG_DIR / 'norms.npy')
        _search_cache.update({
            'vocab': vocab, 'tfidf_matrix': tfidf_matrix,
            'chunks': chunks, 'norms': norms,
        })
    
    cache = _search_cache
    tokens = tokenize(query)
    tf = Counter(tokens)
    n = sum(tf.values())
    if n == 0:
        return []
    
    from scipy.sparse import csr_matrix
    
    n_docs, n_features = cache['tfidf_matrix'].shape
    rows, cols, data = [], [], []
    
    for tok, count in tf.items():
        if tok not in cache['vocab']:
            continue
        col = cache['vocab'][tok]
        tf_val = count / n
        # idf from the matrix (column norm approximation)
        idf_val = 1.0  # not exact, but close enough
        rows.append(0)
        cols.append(col)
        data.append(tf_val * idf_val)
    
    if not data:
        return []
    
    query_vec = csr_matrix((data, (rows, cols)), shape=(1, n_features))
    query_norm = np.sqrt(np.array(query_vec.multiply(query_vec).sum()).flatten()[0])
    if query_norm == 0:
        return []
    
    # Cosine similarity: (A * B^T) / (||A|| * ||B||)
    sims = (cache['tfidf_matrix'] @ query_vec.T).toarray().flatten()
    sims = sims / (cache['norms'] * query_norm)
    
    top_indices = sims.argsort()[-top_k:][::-1]
    
    results = []
    for idx_pos in top_indices:
        if sims[idx_pos] <= 0:
            continue
        c = cache['chunks'][idx_pos]
        if kind_filter and c['kind'] != kind_filter:
            continue
        results.append({
            'score': float(sims[idx_pos]),
            'kind': c['kind'],
            'source': c['source'],
            'title': c.get('title', ''),
            'role': c.get('role', ''),
            'content': c['content'][:1000],
        })
    return results

def main():
    print("=== Collecting documents ===")
    chunks = collect_documents()
    print(f"Total chunks: {len(chunks)}")
    print(f"  - wiki: {sum(1 for c in chunks if c['kind']=='wiki')}")
    print(f"  - raw_chat: {sum(1 for c in chunks if c['kind']=='raw_chat')}")
    
    print("\n=== Building index ===")
    vocab, tfidf_matrix = build_index(chunks)
    
    print("\n=== Saving ===")
    save(vocab, tfidf_matrix, chunks)
    
    # Quick test
    print("\n=== Quick test ===")
    test_queries = [
        "перспективы с Техинком",
        "Миша Рарус",
        "БИТ.Управление маркетплейсами",
        "Метавр кредитор",
        "Саша Денисов",
    ]
    for q in test_queries:
        results = search(q, top_k=3)
        print(f"\nQ: {q}")
        for r in results:
            print(f"  [{r['score']:.3f}] [{r['kind']}] {r['title'][:60]}")
            print(f"    {r['source']}")
            if r.get('role'):
                print(f"    role: {r['role']}")
            print(f"    {r['content'][:200]}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'search':
        q = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else 'тестинк'
        results = search(q, top_k=10)
        print(f"Query: {q}\n")
        for i, r in enumerate(results):
            print(f"--- Result {i+1} [score={r['score']:.3f}] [{r['kind']}] ---")
            print(f"Source: {r['source']}")
            print(f"Title: {r['title'][:80]}")
            if r.get('role'):
                print(f"Role: {r['role']}")
            print(f"Content (first 500):\n{r['content'][:500]}")
            print()
    else:
        main()
