#!/usr/bin/env python3
"""
Daily Blog Generator for TheJorgeRamirezGroup.com
Writes draft posts to blog-staging/ for Teddy to review before pushing.

Usage: python3 daily-blog.py [--topic "custom topic"] [--town "town-slug"]
"""

import os
import sys
import json
import subprocess
from datetime import datetime

WORKSPACE = "/Users/teddy/.openclaw/workspace/TheJorgeRamirezGroup2"
STAGING = os.path.join(WORKSPACE, "blog-staging")
BLOG = os.path.join(WORKSPACE, "blog")
QUEUE_FILE = os.path.join(WORKSPACE, "data", "blog-queue.json")

os.makedirs(STAGING, exist_ok=True)
os.makedirs(os.path.join(WORKSPACE, "data"), exist_ok=True)

# Towns not yet covered — add as we go
TOWN_QUEUE = [
    {"town": "berkeley-heights", "name": "Berkeley Heights", "county": "Union County"},
    {"town": "new-brunswick", "name": "New Brunswick", "county": "Middlesex County"},
    {"town": "piscataway", "name": "Piscataway", "county": "Middlesex County"},
    {"town": "east-brunswick", "name": "East Brunswick", "county": "Middlesex County"},
    {"town": "north-brunswick", "name": "North Brunswick", "county": "Middlesex County"},
    {"town": "bound-brook", "name": "Bound Brook", "county": "Somerset County"},
    {"town": "bridgewater", "name": "Bridgewater", "county": "Somerset County"},
    {"town": "mountainside", "name": "Mountainside", "county": "Union County"},
    {"town": "new-providence", "name": "New Providence", "county": "Union County"},
    {"town": "warren-township", "name": "Warren Township", "county": "Somerset County"},
    {"town": "long-hill", "name": "Long Hill Township", "county": "Morris County"},
    {"town": "chatham-township", "name": "Chatham Township", "county": "Morris County"},
    {"town": "hanover-township", "name": "Hanover Township", "county": "Morris County"},
    {"town": "parsippany-troy-hills", "name": "Parsippany-Troy Hills", "county": "Morris County"},
    {"town": "rockaway-township", "name": "Rockaway Township", "county": "Morris County"},
    {"town": "roxbury", "name": "Roxbury Township", "county": "Morris County"},
    {"town": "washington-township", "name": "Washington Township", "county": "Morris County"},
    {"town": "mine-hill", "name": "Mine Hill Township", "county": "Morris County"},
    {"town": "wharton", "name": "Wharton", "county": "Morris County"},
    {"town": "netcong", "name": "Netcong", "county": "Morris County"},
    {"town": "kearny", "name": "Kearny", "county": "Hudson County"},
    {"town": "bayonne", "name": "Bayonne", "county": "Hudson County"},
    {"town": "union-city", "name": "Union City", "county": "Hudson County"},
    {"town": "north-bergen", "name": "North Bergen", "county": "Hudson County"},
    {"town": "weehawken", "name": "Weehawken", "county": "Hudson County"},
    {"town": "secaucus", "name": "Secaucus", "county": "Hudson County"},
    {"town": "harrison", "name": "Harrison", "county": "Hudson County"},
    {"town": "east-newark", "name": "East Newark", "county": "Hudson County"},
    {"town": "belleville", "name": "Belleville", "county": "Essex County"},
    {"town": "cedar-grove", "name": "Cedar Grove", "county": "Essex County"},
    {"town": "east-orange", "name": "East Orange", "county": "Essex County"},
    {"town": "irvington", "name": "Irvington", "county": "Essex County"},
    {"town": "newark", "name": "Newark", "county": "Essex County"},
    {"town": "orange", "name": "Orange", "county": "Essex County"},
    {"town": "roseland", "name": "Roseland", "county": "Essex County"},
    {"town": "south-caldwell", "name": "South Caldwell", "county": "Essex County"},
    {"town": "west-caldwell", "name": "West Caldwell", "county": "Essex County"},
]

# Topical post ideas (non-town specific)
TOPIC_QUEUE = [
    "How to sell your home in New Jersey without an agent (and why most people regret it)",
    "The truth about FSBO in NJ: what the data actually shows",
    "Best school districts in Union County NJ for families buying in 2026",
    "How long does it take to sell a house in NJ in 2026?",
    "NJ property tax explained: what buyers need to know before closing",
    "How to buy a home in NJ with bad credit in 2026",
    "The hidden costs of buying a home in New Jersey",
    "Best commuter towns to NYC in NJ under $500K",
    "What is a buyer's agent and do I need one in NJ?",
    "How to win a bidding war in NJ's competitive real estate market",
    "New Jersey first-time homebuyer programs and grants in 2026",
    "What NJ home inspectors actually look for (and what to watch out for)",
    "How to stage your NJ home for maximum sale price",
    "Expired listings in NJ: why homes don't sell and how to fix it",
    "Should I buy or rent in New Jersey in 2026?",
]


def get_next_town():
    """Get the next town from the queue that doesn't have a buying post yet."""
    existing = set(os.listdir(BLOG))
    for t in TOWN_QUEUE:
        slug = t["town"]
        if f"buying-home-{slug}-nj-2026.html" not in existing:
            return t
    return None


def get_next_topic():
    """Get a topic that hasn't been written yet."""
    if not os.path.exists(QUEUE_FILE):
        state = {"used_topics": []}
    else:
        with open(QUEUE_FILE) as f:
            state = json.load(f)
    
    used = set(state.get("used_topics", []))
    for topic in TOPIC_QUEUE:
        if topic not in used:
            return topic
    return None


def generate_with_leo(prompt):
    """Run Leo (llama3.3:70b-instruct-q2_K) via ollama to generate content."""
    result = subprocess.run(
        ["ollama", "run", "llama3.3:70b-instruct-q2_K", prompt],
        capture_output=True, text=True, timeout=600
    )
    return result.stdout.strip()


def build_town_post(town_data):
    """Generate a buying guide blog post for a given town."""
    town = town_data["name"]
    county = town_data["county"]
    slug = town_data["town"]
    date = datetime.now().strftime("%B %d, %Y")
    
    prompt = f"""Write a detailed, SEO-optimized blog post for a real estate agent website about buying a home in {town}, NJ ({county}).

REQUIREMENTS:
- Title: "Buying a Home in {town}, NJ in 2026: The Complete Guide"
- Length: 800-1000 words
- Tone: Expert local advisor, Brandon Mulrenin Reverse Selling style — never pushy, pull them in with value
- Include: neighborhood overview, commute to NYC, school district info, typical price range, what to expect in the market, tips for buyers
- End with a soft CTA to contact Jorge Ramirez at The Jorge Ramirez Group, Keller Williams Premier Properties (908-230-7844)
- Format: HTML body content only (no <html>/<head> tags), use <h1>, <h2>, <p> tags
- Include 2-3 NEPQ-style questions naturally in the content (e.g. "What's been the biggest challenge in your home search so far?")
- Do NOT use fake statistics — use general language like "typically" and "in most cases"

Output ONLY the HTML content, no explanation."""

    content = generate_with_leo(prompt)
    
    filename = f"buying-home-{slug}-nj-2026.html"
    filepath = os.path.join(STAGING, filename)
    
    full_html = f"""<!DOCTYPE html>
<html lang="en-US">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Buying a Home in {town}, NJ in 2026 | The Jorge Ramirez Group</title>
<meta name="description" content="Complete guide to buying a home in {town}, NJ. Local market insights, neighborhood info, and expert advice from Jorge Ramirez at Keller Williams.">
<link rel="canonical" href="https://www.thejorgeramirezgroup.com/blog/{filename}">
<link rel="stylesheet" href="/css/style.css">
</head>
<body>
<nav class="site-nav"><div class="nav-container">
  <a href="/" class="nav-logo">The Jorge Ramirez Group</a>
  <div class="nav-links"><a href="/">Home</a><a href="/blog/">Blog</a><a href="/index.html#contact">Contact</a></div>
</div></nav>
<main class="blog-post" style="max-width:800px;margin:0 auto;padding:80px 20px 60px;">
{content}
</main>
<footer class="site-footer"><div class="container">
  <p>© 2026 The Jorge Ramirez Group · Keller Williams Premier Properties · 908-230-7844</p>
</div></footer>
</body>
</html>"""
    
    with open(filepath, "w") as f:
        f.write(full_html)
    
    return filename, filepath


def generate_topic_post(topic):
    """Generate a topical blog post."""
    date = datetime.now().strftime("%B %d, %Y")
    slug = topic.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("'", "").replace(",", "")[:60]
    filename = f"{slug}-{datetime.now().year}.html"
    
    prompt = f"""Write a detailed, SEO-optimized blog post for a real estate agent website in New Jersey.

TOPIC: {topic}

REQUIREMENTS:
- Length: 800-1000 words  
- Tone: Expert local NJ advisor, Brandon Mulrenin Reverse Selling style — never pushy, pull them in with value
- Focus on Union, Essex, Morris, Hudson, Middlesex Counties NJ where relevant
- End with a soft CTA to contact Jorge Ramirez at The Jorge Ramirez Group, Keller Williams Premier Properties (908-230-7844)
- Format: HTML body content only (no <html>/<head> tags), use <h1>, <h2>, <p> tags
- Include 2-3 NEPQ-style questions naturally (e.g. "What's been holding you back from making a move?")
- Do NOT use fake statistics — use general language like "typically" and "in most cases"

Output ONLY the HTML content, no explanation."""

    content = generate_with_leo(prompt)
    
    filepath = os.path.join(STAGING, filename)
    
    full_html = f"""<!DOCTYPE html>
<html lang="en-US">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{topic} | The Jorge Ramirez Group</title>
<meta name="description" content="{topic}. Expert NJ real estate advice from Jorge Ramirez at Keller Williams Premier Properties.">
<link rel="stylesheet" href="/css/style.css">
</head>
<body>
<nav class="site-nav"><div class="nav-container">
  <a href="/" class="nav-logo">The Jorge Ramirez Group</a>
  <div class="nav-links"><a href="/">Home</a><a href="/blog/">Blog</a><a href="/index.html#contact">Contact</a></div>
</div></nav>
<main class="blog-post" style="max-width:800px;margin:0 auto;padding:80px 20px 60px;">
{content}
</main>
<footer class="site-footer"><div class="container">
  <p>© 2026 The Jorge Ramirez Group · Keller Williams Premier Properties · 908-230-7844</p>
</div></footer>
</body>
</html>"""
    
    with open(filepath, "w") as f:
        f.write(full_html)
    
    # Mark topic as used
    if not os.path.exists(QUEUE_FILE):
        state = {"used_topics": []}
    else:
        with open(QUEUE_FILE) as f:
            state = json.load(f)
    state["used_topics"].append(topic)
    with open(QUEUE_FILE, "w") as f:
        json.dump(state, f, indent=2)
    
    return filename, filepath


if __name__ == "__main__":
    print("=== Daily Blog Generator ===")
    
    # Generate town post
    town = get_next_town()
    if town:
        print(f"Generating town post: {town['name']}...")
        fname, fpath = build_town_post(town)
        print(f"✅ Town post saved to staging: {fname}")
    else:
        print("No more towns in queue.")
    
    # Generate topical post
    topic = get_next_topic()
    if topic:
        print(f"Generating topic post: {topic[:50]}...")
        fname, fpath = generate_topic_post(topic)
        print(f"✅ Topic post saved to staging: {fname}")
    else:
        print("No more topics in queue.")
    
    print("\nDone. Posts are in blog-staging/ — Teddy will review before pushing.")
