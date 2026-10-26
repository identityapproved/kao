def search(query, data, category=None, limit=None):
    if query is None:
        query = ""
    if not isinstance(query, str):
        query = str(query)
    tokens = query.lower().split()

    if category is not None:
        data = [e for e in data if e[3] == category]

    if not tokens:
        result = list(data)
        if limit is not None:
            result = result[:limit]
        return result

    scored = []
    for index, entry in enumerate(data):
        text = entry[0]
        tags_str = entry[2]
        cat = entry[3]
        tags = tags_str.split()
        text_l = text.lower()
        cat_l = cat.lower()
        tags_l = [t.lower() for t in tags]

        total = 0
        ok = True
        for token in tokens:
            if token.startswith("tag:"):
                q = token[4:]
                score = 0
                matched = False
                for t in tags_l:
                    if t == q:
                        score = 3
                        matched = True
                    elif t.startswith(q) and score < 2:
                        score = 2
                        matched = True
                    elif q in t and score < 1:
                        score = 1
                        matched = True
                if not matched:
                    ok = False
                    break
                total += score
            elif token.startswith("cat:"):
                q = token[4:]
                if cat_l == q:
                    total += 3
                elif q in cat_l:
                    total += 1
                else:
                    ok = False
                    break
            else:
                score = 0
                matched = False
                for t in tags_l:
                    if t == token:
                        if score < 3:
                            score = 3
                        matched = True
                    elif t.startswith(token):
                        if score < 2:
                            score = 2
                        matched = True
                    elif token in t:
                        if score < 1:
                            score = 1
                        matched = True
                if cat_l == token:
                    if score < 3:
                        score = 3
                    matched = True
                elif token in cat_l:
                    if score < 1:
                        score = 1
                    matched = True
                if token in text_l:
                    if score < 1:
                        score = 1
                    matched = True
                if not matched:
                    ok = False
                    break
                total += score

        if ok:
            scored.append((-total, index, entry))

    scored.sort(key=lambda x: (x[0], x[1]))
    result = [e[2] for e in scored]
    if limit is not None:
        result = result[:limit]
    return result
