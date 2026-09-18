from zeno.tools.docgen import generate_pdf, generate_pptx


def test_generate_pdf_creates_real_file(tmp_path):
    out = tmp_path / "report.pdf"
    result = generate_pdf(out, "Test Report", [("Section 1", "Body text here.")])
    assert result.exists()
    assert result.stat().st_size > 0
    with open(result, "rb") as f:
        assert f.read(4) == b"%PDF"


def test_generate_pptx_creates_real_file(tmp_path):
    out = tmp_path / "deck.pptx"
    result = generate_pptx(out, "Test Deck", [("Slide 1", "Bullet content")])
    assert result.exists()
    assert result.stat().st_size > 0
