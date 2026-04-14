import urllib.request
import json
import re
import os

def fetch_article_data(article_url, article_title):
    """Fetch image, text and clean title from a single article page."""
    try:
        art_req = urllib.request.Request(article_url, headers={'User-Agent': 'Mozilla/5.0'})
        art_html = urllib.request.urlopen(art_req).read().decode('utf-8')
    except Exception as e:
        print(f"  Fehler beim Abrufen von {article_url}: {e}")
        return None

    og_image = re.search(r'<meta property="og:image"\s+content=["\']([^"\']+)["\']', art_html)
    if og_image:
        img_url = og_image.group(1)
    else:
        # Fallback auf erstes Bild
        img_match = re.search(r'<img\s+[^>]*src=["\']([^"\']+)["\']', art_html)
        img_url = img_match.group(1) if img_match else None

    if not img_url:
        print(f"  Konnte kein Bild finden für: {article_url}")
        return None

    # Extract article text
    paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', art_html, re.DOTALL | re.IGNORECASE)
    article_texts = []
    ignore_phrases = ["usethenews", "geschäftsstelle", "bild der woche:", "das material für die lehrperson", "das aktuelle", "willst du", "interessierst du", "markus spillmann"]
    
    for p in paragraphs:
        text = re.sub(r'<[^>]+>', '', p).strip()
        text_lower = text.lower()
        # Filter paragraphs that are too short or contain known boilerplate
        if len(text) > 40 and not any(phrase in text_lower for phrase in ignore_phrases):
            # Clean up common HTML entities
            text = text.replace('&#8220;', '"').replace('&#8222;', '"').replace('&#8211;', '-')
            article_texts.append(text)
            
    article_text = "\n\n".join(article_texts)

    # Titel auch nochmal bereinigen
    clean_title = article_title.replace('&#8211;', '-')
    clean_title = re.sub(r'(Sek\s+I+\s*)*(\d{2}\.\d{2}\.\d{4})?[,\s]*(UseTheNews)?\s*$', '', clean_title).strip()

    return {
        "title": clean_title,
        "imageUrl": img_url,
        "articleUrl": article_url,
        "articleText": article_text
    }


def fetch_and_save():
    url = 'https://usethenews.ch'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        print("Fehler beim Abrufen der Homepage:", e)
        return

    # Suchen wir nach allen Links für Bild der Woche
    links = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
    
    # Sammle alle passenden Artikel-URLs
    candidates = []  # Liste von (url, title) Tupeln
    seen_urls = set()

    for href, text in links:
        text_lower = text.lower()
        if 'bild der woche' in text_lower:
            # Filtere Artikel heraus, die EXPLIZIT nur für Sek I sind
            if 'sek i' in text_lower and 'sek ii' not in text_lower:
                continue
            # Filtere Making-of Artikel heraus
            if 'making-of' in text_lower or 'making of' in text_lower:
                continue

            full_url = href if href.startswith('http') else url + href
            raw_title = re.sub(r'<[^>]+>', '', text).strip()
            # Entferne angehängte Metadaten wie "Sek I Sek II dd.mm.yyyy, UseTheNews"
            clean_title = re.sub(r'(Sek\s+I+\s*)*(\d{2}\.\d{2}\.\d{4})?[,\s]*(UseTheNews)?\s*$', '', raw_title).strip()
            
            if '/category/' in full_url:
                # Kategorie-Seite: Artikel daraus extrahieren
                try:
                    cat_req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
                    cat_html = urllib.request.urlopen(cat_req).read().decode('utf-8')
                    article_links = re.findall(r'<h[23][^>]*>\s*<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', cat_html, re.IGNORECASE | re.DOTALL)
                    for link, title in article_links:
                        title_text = re.sub(r'<[^>]+>', '', title).strip()
                        title_lower = title_text.lower()
                        if 'sek i' in title_lower and 'sek ii' not in title_lower:
                            continue
                        if 'making-of' in title_lower or 'making of' in title_lower:
                            continue
                        full_link = link if link.startswith('http') else url + link
                        if full_link not in seen_urls:
                            seen_urls.add(full_link)
                            candidates.append((full_link, title_text))
                except Exception as e:
                    print(f"Fehler beim Abrufen der Kategorie-Seite: {e}")
            else:
                if full_url not in seen_urls:
                    seen_urls.add(full_url)
                    candidates.append((full_url, clean_title))

    if not candidates:
        print("Konnte keine Artikel finden.")
        return

    # Maximal 3 Artikel verarbeiten
    max_articles = 3
    articles = []
    
    for article_url, article_title in candidates[:max_articles]:
        print(f"Verarbeite: {article_title}")
        data = fetch_article_data(article_url, article_title)
        if data:
            articles.append(data)

    if not articles:
        print("Konnte keine Artikel-Daten extrahieren.")
        return

    # Speichern als json im gleichen Ordner
    file_path = os.path.join(os.path.dirname(__file__), 'news_data.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=4)
    print(f"Daten erfolgreich aktualisiert: {len(articles)} Artikel in news_data.json gespeichert.")

if __name__ == '__main__':
    fetch_and_save()
