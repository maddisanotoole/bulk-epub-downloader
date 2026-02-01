import pytest
from scraper_utils import parse_article_html, format_author_name


def test_format_author_name():
    """Test author name formatting"""
    assert format_author_name("J.K. Rowling") == "jk-rowling"
    assert format_author_name("  John Doe  ") == "john-doe"
    assert format_author_name("Name, Jr.") == "name-jr"
    assert format_author_name("UPPER CASE") == "upper-case"


def test_parse_article_html_basic():
    """Test parsing article HTML with basic structure"""
    html = """
    <article>
        <h2 class="entry-title">
            <a href="https://example.com/book">Test Book Title</a>
        </h2>
        <time class="entry-time">January 1, 2026</time>
        <div class="postmetainfo">
            <strong>Author:</strong> John Doe<br>
            <strong>Language:</strong> English<br>
            <strong>Genre:</strong> Fiction
        </div>
        <a class="entry-image-link">
            <img src="https://example.com/image.jpg" />
        </a>
        <div class="entry-content">
            <p>Book description here [EPUB] [PDF]</p>
        </div>
    </article>
    """
    
    result = parse_article_html(html)
    
    assert result['title'] == 'Test Book Title'
    assert result['book_url'] == 'https://example.com/book'
    assert result['date'] == 'January 1, 2026'
    assert result['book_author'] == 'John Doe'
    assert result['language'] == 'English'
    assert result['genre'] == 'Fiction'
    assert result['image_url'] == 'https://example.com/image.jpg'
    assert result['has_epub'] is True
    assert result['has_pdf'] is True


def test_parse_article_html_epub_only():
    """Test parsing article with only EPUB"""
    html = """
    <article>
        <h2 class="entry-title">
            <a href="https://example.com/book">Test Book [EPUB]</a>
        </h2>
        <div class="entry-content">
            <p>Description without PDF</p>
        </div>
    </article>
    """
    
    result = parse_article_html(html)
    
    assert result['has_epub'] is True
    assert result['has_pdf'] is False


def test_parse_article_html_missing_fields():
    """Test parsing article with missing optional fields"""
    html = """
    <article>
        <h2 class="entry-title">
            <a href="https://example.com/book">Minimal Book</a>
        </h2>
    </article>
    """
    
    result = parse_article_html(html)
    
    assert result['title'] == 'Minimal Book'
    assert result['book_url'] == 'https://example.com/book'
    assert result['book_author'] == ''
    assert result['language'] == ''
    assert result['genre'] == ''
    assert result['has_epub'] is False
    assert result['has_pdf'] is False


def test_parse_article_html_data_src_image():
    """Test parsing image with data-src attribute"""
    html = """
    <article>
        <h2 class="entry-title">
            <a href="https://example.com/book">Test Book</a>
        </h2>
        <a class="entry-image-link">
            <img data-src="https://example.com/lazy-image.jpg" />
        </a>
    </article>
    """
    
    result = parse_article_html(html)
    
    assert result['image_url'] == 'https://example.com/lazy-image.jpg'
