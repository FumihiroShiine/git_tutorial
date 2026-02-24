#!/usr/bin/env python3
"""MyNews - Fetch RSS feeds and generate a static HTML dashboard."""

import html
import re
import sys
import urllib.request
from datetime import datetime

import feedparser

FEEDS = [
    {
        "name": "Import AI",
        "slug": "import-ai",
        "url": "https://importai.substack.com/feed",
        "icon": "\U0001f916",
        "color": "#6366f1",
        "max_items": 5,
    },
    {
        "name": "Simon Willison",
        "slug": "simon-willison",
        "url": "https://simonwillison.net/atom/everything/",
        "icon": "\U0001f4bb",
        "color": "#059669",
        "max_items": 10,
    },
    {
        "name": "Lenny's Newsletter",
        "slug": "lennys-newsletter",
        "url": "https://www.lennysnewsletter.com/feed",
        "icon": "\U0001f4ca",
        "color": "#d97706",
        "max_items": 5,
    },
    {
        "name": "NN/g",
        "slug": "nng",
        "url": "https://www.nngroup.com/feed/rss/",
        "icon": "\U0001f52c",
        "color": "#dc2626",
        "max_items": 5,
    },
    {
        "name": "Maggie Appleton",
        "slug": "maggie-appleton",
        "url": "https://maggieappleton.com/rss.xml",
        "icon": "\U0001f33f",
        "color": "#16a34a",
        "max_items": 5,
    },
]


def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def truncate(text, max_len=200):
    """Truncate text to max_len characters."""
    if len(text) <= max_len:
        return text
    return text[:max_len].rsplit(" ", 1)[0] + "..."


def fetch_feed(feed_config):
    """Fetch and parse a single RSS/Atom feed."""
    url = feed_config["url"]
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "MyNews/1.0 (+https://github.com)"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
        parsed = feedparser.parse(raw)
    except Exception as e:
        print(f"Warning: Failed to fetch {feed_config['name']}: {e}", file=sys.stderr)
        return []

    articles = []
    for entry in parsed.entries[: feed_config["max_items"]]:
        date_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        if date_parsed:
            dt = datetime(*date_parsed[:6])
            date_str = dt.strftime("%Y-%m-%d")
            sort_key = dt.timestamp()
        else:
            date_str = ""
            sort_key = 0

        summary_raw = entry.get("summary", "")
        summary = truncate(strip_html(summary_raw))

        articles.append(
            {
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", "#"),
                "date": date_str,
                "sort_key": sort_key,
                "summary": summary,
                "source_name": feed_config["name"],
                "source_slug": feed_config["slug"],
                "source_icon": feed_config["icon"],
                "source_color": feed_config["color"],
            }
        )
    return articles


def generate_html(articles, updated_at):
    """Generate the full HTML page."""
    # Build filter buttons
    filter_buttons = '<button class="filter-btn active" data-source="all">All</button>\n'
    for feed in FEEDS:
        filter_buttons += (
            f'        <button class="filter-btn" data-source="{feed["slug"]}">'
            f'{feed["icon"]} {feed["name"]}</button>\n'
        )

    # Build article cards
    cards = ""
    for a in articles:
        title_escaped = html.escape(a["title"])
        summary_escaped = html.escape(a["summary"])
        link_escaped = html.escape(a["link"])
        cards += f"""      <article class="card" data-source="{a['source_slug']}" style="border-left-color: {a['source_color']}">
        <div class="card-meta">
          <span class="source-badge" style="color: {a['source_color']}">{a['source_icon']} {html.escape(a['source_name'])}</span>
          <time datetime="{a['date']}">{a['date']}</time>
        </div>
        <h2><a href="{link_escaped}" target="_blank" rel="noopener noreferrer">{title_escaped}</a></h2>
        <p class="summary">{summary_escaped}</p>
      </article>
"""

    if not cards:
        cards = '      <p class="empty">No articles available. Try running the build again later.</p>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MyNews</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      padding: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      line-height: 1.6;
      color: #1a1a2e;
      background: #f8f9fa;
    }}

    header {{
      background: #fff;
      border-bottom: 1px solid #e2e8f0;
      padding: 24px 32px 16px;
    }}

    header h1 {{
      margin: 0 0 4px;
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.5px;
    }}

    .updated {{
      margin: 0;
      font-size: 13px;
      color: #64748b;
    }}

    .filters {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      padding: 16px 32px;
      background: #fff;
      border-bottom: 1px solid #e2e8f0;
    }}

    .filter-btn {{
      padding: 6px 14px;
      border: 1px solid #e2e8f0;
      border-radius: 20px;
      background: #fff;
      cursor: pointer;
      font-size: 13px;
      color: #475569;
      transition: all 0.15s ease;
    }}

    .filter-btn:hover {{
      background: #f1f5f9;
    }}

    .filter-btn.active {{
      background: #1a1a2e;
      color: #fff;
      border-color: #1a1a2e;
    }}

    main {{
      max-width: 960px;
      margin: 24px auto;
      padding: 0 24px;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 16px;
    }}

    .card {{
      background: #fff;
      border-radius: 8px;
      padding: 20px;
      border-left: 4px solid #e2e8f0;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      transition: box-shadow 0.15s ease;
    }}

    .card:hover {{
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }}

    .card-meta {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 13px;
    }}

    .source-badge {{
      font-weight: 600;
    }}

    time {{
      color: #94a3b8;
    }}

    .card h2 {{
      margin: 0 0 8px;
      font-size: 17px;
      font-weight: 600;
      line-height: 1.4;
    }}

    .card h2 a {{
      color: #1a1a2e;
      text-decoration: none;
    }}

    .card h2 a:hover {{
      color: #4f46e5;
      text-decoration: underline;
    }}

    .summary {{
      margin: 0;
      font-size: 14px;
      color: #64748b;
      line-height: 1.5;
    }}

    .empty {{
      grid-column: 1 / -1;
      text-align: center;
      color: #94a3b8;
      font-size: 16px;
      padding: 48px 0;
    }}

    @media (prefers-color-scheme: dark) {{
      body {{
        background: #0f172a;
        color: #e2e8f0;
      }}

      header {{
        background: #1e293b;
        border-bottom-color: #334155;
      }}

      .updated {{
        color: #94a3b8;
      }}

      .filters {{
        background: #1e293b;
        border-bottom-color: #334155;
      }}

      .filter-btn {{
        background: #1e293b;
        border-color: #334155;
        color: #cbd5e1;
      }}

      .filter-btn:hover {{
        background: #334155;
      }}

      .filter-btn.active {{
        background: #e2e8f0;
        color: #0f172a;
        border-color: #e2e8f0;
      }}

      .card {{
        background: #1e293b;
        box-shadow: 0 1px 3px rgba(0,0,0,0.2);
      }}

      .card:hover {{
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      }}

      .card h2 a {{
        color: #e2e8f0;
      }}

      .card h2 a:hover {{
        color: #818cf8;
      }}

      .summary {{
        color: #94a3b8;
      }}

      time {{
        color: #64748b;
      }}
    }}

    @media (max-width: 480px) {{
      header {{
        padding: 16px;
      }}

      .filters {{
        padding: 12px 16px;
      }}

      main {{
        padding: 0 12px;
        margin: 16px auto;
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>MyNews</h1>
    <p class="updated">Last updated: {updated_at}</p>
  </header>
  <nav class="filters">
    {filter_buttons}
  </nav>
  <main>
{cards}
  </main>
  <script>
    document.querySelectorAll('.filter-btn').forEach(function(btn) {{
      btn.addEventListener('click', function() {{
        var source = this.dataset.source;
        document.querySelectorAll('.card').forEach(function(card) {{
          card.style.display = (source === 'all' || card.dataset.source === source) ? '' : 'none';
        }});
        document.querySelectorAll('.filter-btn').forEach(function(b) {{
          b.classList.toggle('active', b === btn);
        }});
      }});
    }});
  </script>
</body>
</html>
"""


def main():
    print("Fetching feeds...")
    all_articles = []
    for feed_config in FEEDS:
        print(f"  Fetching {feed_config['name']}...")
        articles = fetch_feed(feed_config)
        print(f"    Got {len(articles)} articles")
        all_articles.extend(articles)

    if not all_articles:
        print("Error: No articles fetched from any source.", file=sys.stderr)
        sys.exit(1)

    all_articles.sort(key=lambda a: a["sort_key"], reverse=True)

    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    html_content = generate_html(all_articles, updated_at)

    output_path = "index.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated {output_path} with {len(all_articles)} articles.")


if __name__ == "__main__":
    main()
