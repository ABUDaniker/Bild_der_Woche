import urllib.request
import json
import re
import os

def fetch_and_save():
    url = 'https://usethenews.ch'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')
    except Exception as e:
        print("Fehler beim Abrufen der Homepage:", e)
        return

    # Suchen wir nach dem Link für Bild der Woche
    links = re.findall(r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.IGNORECASE | re.DOTALL)
    
    target_url = None
    target_title = None

    for href, text in links:
        text_lower = text.lower()
        if 'bild der woche' in text_lower:
            # Filtere Artikel heraus, die EXPLIZIT nur für Sek I sind
            if 'sek i' in text_lower and 'sek ii' not in text_lower:
                continue
            # Filtere Making-of Artikel heraus
            if 'making-of' in text_lower or 'making of' in text_lower:
                continue

            target_url = href if href.startswith('http') else url + href
            raw_title = re.sub(r'<[^>]+>', '', text).strip()
            # Entferne angehängte Metadaten wie "Sek I Sek II dd.mm.yyyy, UseTheNews"
            target_title = re.sub(r'(Sek\s+I+\s*)*(\d{2}\.\d{2}\.\d{4})?[,\s]*(UseTheNews)?\s*$', '', raw_title).strip()
            if '/category/' not in target_url:
                break

    if target_url and '/category/' in target_url:
        cat_req = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0'})
        cat_html = urllib.request.urlopen(cat_req).read().decode('utf-8')
        # Versuchen wir den ersten Sek II Artikel-Link zu finden
        article_links = re.findall(r'<h[23][^>]*>\s*<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', cat_html, re.IGNORECASE | re.DOTALL)
        found_article = False
        if article_links:
            for link, title in article_links:
                title_lower = title.lower()
                if 'sek i' in title_lower and 'sek ii' not in title_lower:
                    continue
                target_url = link
                target_title = re.sub(r'<[^>]+>', '', title).strip()
                found_article = True
                break
                
            if not found_article:
                target_url = article_links[0][0]
                target_title = re.sub(r'<[^>]+>', '', article_links[0][1]).strip()

    if not target_url:
        print("Konnte keinen Artikel finden.")
        return

    # Hole Artikel für das Bild
    art_req = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0'})
    art_html = urllib.request.urlopen(art_req).read().decode('utf-8')
    
    og_image = re.search(r'<meta property="og:image"\s+content=["\']([^"\']+)["\']', art_html)
    if og_image:
        img_url = og_image.group(1)
    else:
        # Fallback auf erstes Bild
        img_match = re.search(r'<img\s+[^>]*src=["\']([^"\']+)["\']', art_html)
        img_url = img_match.group(1) if img_match else None

    if not img_url:
        print("Konnte kein Bild finden.")
        return

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
    clean_title = target_title.replace('&#8211;', '-')
    clean_title = re.sub(r'(Sek\s+I+\s*)*(\d{2}\.\d{2}\.\d{4})?[,\s]*(UseTheNews)?\s*$', '', clean_title).strip()

    data = {
        "title": clean_title,
        "imageUrl": img_url,
        "articleUrl": target_url,
        "articleText": article_text
    }

    # Speichern als json im gleichen Ordner
    file_path = os.path.join(os.path.dirname(__file__), 'news_data.json')
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print("Daten erfolgreich aktualisiert und in news_data.json gespeichert:", data)

if __name__ == '__main__':
    fetch_and_save()
