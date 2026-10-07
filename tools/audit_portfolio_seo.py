#!/usr/bin/env python3
"""Read-only crawl of confirmed public sites. No login, form submits or ranking claims.

Produces a dated technical baseline and link graph. Search Console and conversion
data must be collected separately; these checks do not measure search traffic.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import urljoin, urlsplit, urldefrag
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

SITES = ["https://thejorgeramirezgroup.com", "https://www.flylyfe.com",
         "https://aisalespipeline.com", "https://clickmingo.com",
         "https://gigislongbranch.com", "https://gigisnystylepizza.com",
         "https://seabrightbagel.com"]

class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.canonical=[]; self.description=[]; self.title=[]
        self.h1=0; self.links=[]; self.ld=[]; self.robots=[]; self.capture=None
        self.feed(html)
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='title': self.title.append(''); self.capture='title'
        if tag=='h1': self.h1+=1
        if tag=='a' and a.get('href'): self.links.append(a['href'])
        if tag=='link' and a.get('rel')=='canonical': self.canonical.append(a.get('href',''))
        if tag=='meta' and a.get('name')=='description': self.description.append(a.get('content',''))
        if tag=='meta' and a.get('name') in ('robots','googlebot'): self.robots.append(a.get('content',''))
        if tag=='script' and a.get('type')=='application/ld+json': self.ld.append(''); self.capture='ld'
    def handle_endtag(self, tag):
        if tag in ('title','script'): self.capture=None
    def handle_data(self, text):
        if self.capture=='title': self.title[-1]+=text
        if self.capture=='ld': self.ld[-1]+=text

def fetch(url):
    last=None
    for _ in range(2):
        try:
            req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (PublicSiteSEOCheck; read-only)'})
            with urllib.request.urlopen(req, timeout=25) as r:
                return r.url, r.read(8_000_000).decode('utf-8'), r.headers
        except Exception as e: last=e
    raise last

def normalized(url):
    return urldefrag(url)[0].rstrip('/')

def sitemap_locations(tree):
    # Image/video extensions also contain <loc>; only page/sitemap direct
    # children belong in this HTML crawl.
    kind = tree.tag.split('}')[-1]
    item = 'sitemap' if kind == 'sitemapindex' else 'url'
    return [loc.text for node in tree if node.tag.split('}')[-1] == item
            for loc in node if loc.tag.split('}')[-1] == 'loc']

def sitemap_urls(origin):
    pending=[origin+'/sitemap.xml']; seen=set(); urls=[]
    while pending:
        current=pending.pop()
        if current in seen: continue
        if urlsplit(current).netloc!=urlsplit(origin).netloc: raise ValueError('Off-site sitemap: '+current)
        seen.add(current)
        if len(seen)>30: raise ValueError('Sitemap nesting limit exceeded')
        _,xml,_=fetch(current); tree=ET.fromstring(xml)
        locs=sitemap_locations(tree)
        if tree.tag.split('}')[-1]=='sitemapindex': pending.extend(locs)
        else: urls.extend(locs)
    if not urls: raise ValueError('Empty sitemap')
    if len(urls)>2000: raise ValueError('Review scope before crawling more than 2000 pages')
    return urls

def audit_page(url):
    result={'url':url,'errors':[]}
    try:
        final,html,headers=fetch(url); p=Page(html); errors=result['errors']
        if normalized(final)!=normalized(url): errors.append('Sitemap URL redirects: '+final)
        if len(p.canonical)!=1 or normalized(urljoin(final,p.canonical[0]))!=normalized(url): errors.append('Canonical mismatch: '+str(p.canonical))
        if len(p.title)!=1 or not p.title[0].strip(): errors.append('Expected one nonempty title')
        if len(p.description)!=1 or not p.description[0].strip(): errors.append('Expected one nonempty description')
        if p.h1!=1: errors.append('Expected one H1; found '+str(p.h1))
        if 'noindex' in (' '.join(p.robots)+' '+headers.get('X-Robots-Tag','')).lower(): errors.append('Noindex page in sitemap')
        for ld in p.ld:
            try: json.loads(ld)
            except ValueError: errors.append('Invalid JSON-LD JSON')
        result.update(title=p.title,description=p.description,canonical=p.canonical,
                      schema_blocks=len(p.ld),links=sorted(set(urljoin(final,link) for link in p.links)))
    except Exception as e: result['errors'].append(str(e))
    return result

def audit_site(origin):
    site={'origin':origin,'errors':[],'warnings':[],'pages':[]}
    try:
        urls=sitemap_urls(origin)
        if len(urls)!=len(set(urls)): site['errors'].append('Duplicate sitemap URLs')
        if any(urlsplit(u).netloc!=urlsplit(origin).netloc for u in urls): raise ValueError('Unexpected sitemap hostname')
        try:
            _,robots,_=fetch(origin+'/robots.txt'); rules=RobotFileParser(); rules.parse(robots.splitlines())
            for u in urls:
                if not rules.can_fetch('Googlebot',u): site['errors'].append('Robots disallows '+u)
        except Exception as e: site['warnings'].append('Robots could not be checked: '+str(e))
        with ThreadPoolExecutor(max_workers=6) as pool: site['pages']=list(pool.map(audit_page,sorted(set(urls))))
        incoming=Counter()
        for p in site['pages']:
            for link in p.get('links',[]):
                if normalized(link)!=normalized(p['url']): incoming[normalized(link)]+=1
        for p in site['pages']: p['sitemap_page_inlinks']=incoming[normalized(p['url'])]
        site['warnings'] += ['No inbound link from other sitemap pages: '+p['url'] for p in site['pages'] if not p['sitemap_page_inlinks']]
        for key in ('title','description'):
            counts=Counter(p.get(key,[''])[0] for p in site['pages'] if p.get(key))
            site['warnings'] += [f'Duplicate {key} on {count} pages: {value}' for value,count in counts.items() if count>1]
    except Exception as e: site['errors'].append(str(e))
    return site

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--site',action='append',choices=SITES)
    parser.add_argument('--output',default='seo-audit'); args=parser.parse_args()
    report={'checked_at':datetime.now(timezone.utc).isoformat(),'sites':[]}
    for origin in args.site or SITES:
        site=audit_site(origin); report['sites'].append(site)
        print(origin, len(site['pages']), 'pages;', len(site['errors'])+sum(len(p['errors']) for p in site['pages']), 'errors',flush=True)
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Public website technical SEO baseline','',report['checked_at'],'',
           'Read-only checks of sitemap URLs. This is not a ranking, indexing, lead or revenue report.','']
    errors=[]
    for site in report['sites']:
        lines += ['## '+site['origin'],'',f"Checked {len(site['pages'])} sitemap pages.",'']
        findings=site['errors']+[p['url']+': '+e for p in site['pages'] for e in p['errors']]
        errors.extend(findings)
        lines += ['- '+s for s in findings] or ['No metadata, canonical, JSON syntax, H1 or indexing-directive errors found.']
        lines += ['']+['- Review: '+w for w in site['warnings']]+['']
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    raise SystemExit(1 if errors else 0)

if __name__=='__main__':main()
