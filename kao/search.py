def _lines(blob, q):
    # indices of the lines of a newline-joined blob that contain q
    found = []
    index = 0
    prev = 0
    pos = blob.find(q)
    while pos != -1:
        start = blob.rfind(b"\n", 0, pos) + 1
        index += blob.count(b"\n", prev, start)
        prev = start
        found.append(index)
        end = blob.find(b"\n", pos)
        if end == -1:
            break
        pos = blob.find(q, end)
    return found


def _token_hits(db, token):
    # {entry: score}; scores per token: exact 3, prefix 2, substring 1 (categories: exact 3, substring 1)
    kind = None
    if token.startswith("tag:") or token.startswith("cat:"):
        kind, token = token[:3], token[4:]
    if not token:
        return None
    groups = ([], [], [])
    if kind != "cat":
        for w, word in enumerate(db.words()):
            if token in word:
                groups[0 if word == token else 1 if word.startswith(token) else 2].extend(db.word_entries(w))
    if kind != "tag":
        for c, name in enumerate(db.categories):
            if token in name:
                groups[0 if name == token else 2].extend(db.category_entries(c))
    if kind is None:
        # the face itself, e.g. "^_^" or "ω"
        groups[2].extend(_lines(db.faces, token.encode("utf-8")))
    # best score wins: build from the lowest group up so higher scores overwrite (dict ops stay in C)
    hits = {}
    for score, entries in ((1, groups[2]), (2, groups[1]), (3, groups[0])):
        if entries:
            hits.update(dict.fromkeys(entries, score))
    return hits


def search(query, db, category=None, limit=None):
    tokens = (query or "").lower().split()
    cat = None
    if category is not None:
        if category not in db.categories:
            return []
        cat = db.categories.index(category)

    if not tokens:
        if cat is None:
            result = range(db.count)
        else:
            result = sorted(db.category_entries(cat))
        return result if limit is None else result[:limit]

    scores = None
    for token in tokens:
        hits = _token_hits(db, token)
        if hits is None:
            continue
        if scores is None:
            scores = hits
        else:
            scores = {i: s + hits[i] for i, s in scores.items() if i in hits}
        if not scores:
            return []
    if scores is None:
        return search("", db, category, limit)
    if cat is not None:
        scores = {i: scores[i] for i in db.category_entries(cat) if i in scores}
    # index order first, then a stable sort by score keeps ties in data order
    result = sorted(sorted(scores), key=scores.__getitem__, reverse=True)
    return result if limit is None else result[:limit]
