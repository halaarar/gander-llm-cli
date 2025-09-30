from gander_llm_cli.cli import extract_urls, extract_mentions, split_owned_external


def test_extract_urls_simple():
    text = (
        "See [site](https://brand.example.com/page) and also https://example.org/review.\n"
        "Bare link: http://brand.example.com/faq)"
    )
    urls = extract_urls(text)
    assert "https://brand.example.com/page" in urls
    assert "https://example.org/review" in urls  # no trailing period
    assert "http://brand.example.com/faq" in urls  # no trailing parenthesis


def test_extract_mentions_exact():
    text = "I like Gander and Gander GEO. Not gANDer."
    assert extract_mentions(text, "Gander") == ["Gander", "Gander"]


def test_owned_vs_external():
    urls = [
        "https://gandergeo.com/docs",
        "https://sub.gandergeo.com/help",
        "https://example.org/review",
    ]
    owned, external = split_owned_external(urls, "gandergeo.com")
    assert urls[0] in owned and urls[1] in owned
    assert urls[2] in external
