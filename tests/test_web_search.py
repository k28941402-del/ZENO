from zeno.tools.web_search import search_instant_answer


def fake_fetch_with_abstract(url, params):
    return {
        "AbstractText": "Python is a high-level programming language.",
        "AbstractURL": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "RelatedTopics": [],
    }


def fake_fetch_related_only(url, params):
    return {
        "AbstractText": "",
        "RelatedTopics": [{"Text": "Fallback related answer", "FirstURL": "https://example.com"}],
    }


def fake_fetch_no_answer(url, params):
    return {"AbstractText": "", "RelatedTopics": []}


def test_search_returns_abstract_when_present():
    result = search_instant_answer("python", fetch_fn=fake_fetch_with_abstract)
    assert result["has_answer"] is True
    assert "Python" in result["answer"]


def test_search_falls_back_to_related_topics():
    result = search_instant_answer("obscure query", fetch_fn=fake_fetch_related_only)
    assert result["has_answer"] is True
    assert result["answer"] == "Fallback related answer"


def test_search_honestly_reports_no_answer():
    result = search_instant_answer("asdkjhaksjdh", fetch_fn=fake_fetch_no_answer)
    assert result["has_answer"] is False
    assert result["answer"] is None
