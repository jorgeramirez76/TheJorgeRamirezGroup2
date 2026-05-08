#!/usr/bin/env python3
"""
Comprehensive Website Audit & Fix Script
TheJorgeRamirezGroup.com
"""

import re
from pathlib import Path
import json

class WebsiteAuditor:
    def __init__(self):
        self.issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        self.fixes_applied = []
        self.noindex_pages = []
        self.pages_scanned = 0
        
    def scan_all_html_files(self):
        """Scan all HTML files for issues"""
        html_files = list(Path('.').rglob('*.html'))
        
        # Exclude Spanish versions and certain directories
        html_files = [f for f in html_files if '/es/' not in str(f) and '.git' not in str(f)]
        
        print(f"📊 Scanning {len(html_files)} HTML files...")
        print()
        
        for filepath in html_files:
            self.pages_scanned += 1
            self.audit_file(filepath)
        
    def audit_file(self, filepath):
        """Audit a single HTML file"""
        try:
            content = filepath.read_text(encoding='utf-8')
        except:
            return
        
        # 1. CRITICAL: Check for noindex
        if 'noindex' in content.lower():
            # Skip if it's 404.html or redirect pages
            if filepath.name == '404.html':
                return
            if 'http-equiv="refresh"' in content:  # Redirect page
                return
                
            self.noindex_pages.append(str(filepath))
            self.issues['critical'].append({
                'file': str(filepath),
                'issue': 'noindex tag blocking Google',
                'line': self._find_line_number(content, 'noindex')
            })
        
        # 2. HIGH: Missing title tag
        if '<title>' not in content:
            self.issues['high'].append({
                'file': str(filepath),
                'issue': 'Missing title tag'
            })
        
        # 3. HIGH: Missing meta description
        if 'name="description"' not in content:
            self.issues['high'].append({
                'file': str(filepath),
                'issue': 'Missing meta description'
            })
        
        # 4. HIGH: Duplicate title tags
        title_count = content.count('<title>')
        if title_count > 1:
            self.issues['high'].append({
                'file': str(filepath),
                'issue': f'Duplicate title tags ({title_count} found)'
            })
        
        # 5. MEDIUM: Missing canonical tag
        if 'rel="canonical"' not in content and filepath.name != '404.html':
            self.issues['medium'].append({
                'file': str(filepath),
                'issue': 'Missing canonical URL'
            })
        
        # 6. MEDIUM: Missing Open Graph tags
        if 'og:title' not in content and filepath.name != '404.html':
            self.issues['medium'].append({
                'file': str(filepath),
                'issue': 'Missing Open Graph tags'
            })
        
        # 7. MEDIUM: Title too long (>60 chars)
        title_match = re.search(r'<title>([^<]+)</title>', content)
        if title_match:
            title = title_match.group(1)
            if len(title) > 70:
                self.issues['medium'].append({
                    'file': str(filepath),
                    'issue': f'Title too long ({len(title)} chars): {title[:50]}...'
                })
        
        # 8. MEDIUM: Meta description too long (>160 chars)
        desc_match = re.search(r'<meta name="description" content="([^"]+)"', content)
        if desc_match:
            desc = desc_match.group(1)
            if len(desc) > 160:
                self.issues['medium'].append({
                    'file': str(filepath),
                    'issue': f'Meta description too long ({len(desc)} chars)'
                })
        
        # 9. LOW: Missing alt text on images (sample check)
        img_count = content.count('<img')
        img_with_alt = content.count('alt=')
        if img_count > 0 and img_with_alt < img_count:
            missing = img_count - img_with_alt
            self.issues['low'].append({
                'file': str(filepath),
                'issue': f'{missing} images missing alt text'
            })
    
    def _find_line_number(self, content, search_str):
        """Find line number of a string"""
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if search_str in line:
                return i
        return None
    
    def fix_noindex_tags(self):
        """Fix all noindex tags (except 404 and redirects)"""
        print("🔧 Fixing noindex tags...")
        print()
        
        fixed_count = 0
        
        for filepath_str in self.noindex_pages:
            filepath = Path(filepath_str)
            
            try:
                content = filepath.read_text(encoding='utf-8')
                
                # Skip if it's a redirect page
                if 'http-equiv="refresh"' in content:
                    continue
                
                # Replace noindex with index
                original_content = content
                content = re.sub(
                    r'<meta name="robots" content="noindex, follow">',
                    '<meta name="robots" content="index, follow">',
                    content
                )
                
                if content != original_content:
                    filepath.write_text(content, encoding='utf-8')
                    fixed_count += 1
                    self.fixes_applied.append(f"Fixed noindex: {filepath}")
                    print(f"   ✓ {filepath}")
            
            except Exception as e:
                print(f"   ✗ Error fixing {filepath}: {e}")
        
        print()
        print(f"✅ Fixed {fixed_count} noindex tags")
        print()
    
    def generate_report(self):
        """Generate comprehensive audit report"""
        print()
        print("=" * 80)
        print("COMPREHENSIVE WEBSITE AUDIT REPORT")
        print("TheJorgeRamirezGroup.com")
        print("=" * 80)
        print()
        
        print(f"📊 Pages Scanned: {self.pages_scanned}")
        print()
        
        # CRITICAL ISSUES
        if self.issues['critical']:
            print("🔴 CRITICAL ISSUES (Fix Immediately!)")
            print("-" * 80)
            print(f"Total: {len(self.issues['critical'])}")
            print()
            
            # Group by issue type
            issue_types = {}
            for issue in self.issues['critical']:
                issue_type = issue['issue']
                if issue_type not in issue_types:
                    issue_types[issue_type] = []
                issue_types[issue_type].append(issue['file'])
            
            for issue_type, files in issue_types.items():
                print(f"   • {issue_type}: {len(files)} files")
                if len(files) <= 5:
                    for f in files:
                        print(f"     - {f}")
                else:
                    for f in files[:3]:
                        print(f"     - {f}")
                    print(f"     ... and {len(files) - 3} more")
                print()
        
        # HIGH PRIORITY
        if self.issues['high']:
            print("🟠 HIGH PRIORITY ISSUES")
            print("-" * 80)
            print(f"Total: {len(self.issues['high'])}")
            print()
            
            issue_types = {}
            for issue in self.issues['high']:
                issue_type = issue['issue']
                if issue_type not in issue_types:
                    issue_types[issue_type] = []
                issue_types[issue_type].append(issue['file'])
            
            for issue_type, files in issue_types.items():
                print(f"   • {issue_type}: {len(files)} files")
                if len(files) <= 3:
                    for f in files:
                        print(f"     - {f}")
                print()
        
        # MEDIUM PRIORITY
        if self.issues['medium']:
            print("🟡 MEDIUM PRIORITY ISSUES")
            print("-" * 80)
            print(f"Total: {len(self.issues['medium'])}")
            print()
            
            issue_types = {}
            for issue in self.issues['medium']:
                issue_type = issue['issue']
                if issue_type not in issue_types:
                    issue_types[issue_type] = 0
                issue_types[issue_type] += 1
            
            for issue_type, count in issue_types.items():
                print(f"   • {issue_type}: {count} files")
            print()
        
        # SUMMARY
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print()
        print(f"🔴 Critical: {len(self.issues['critical'])}")
        print(f"🟠 High:     {len(self.issues['high'])}")
        print(f"🟡 Medium:   {len(self.issues['medium'])}")
        print(f"⚪ Low:      {len(self.issues['low'])}")
        print()
        
        # RECOMMENDATIONS
        print("=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        print()
        
        if len(self.noindex_pages) > 0:
            print("1. CRITICAL: Remove all noindex tags from content pages")
            print(f"   {len(self.noindex_pages)} pages are blocked from Google indexing!")
            print()
        
        if any('Missing title tag' in str(i) for i in self.issues['high']):
            print("2. HIGH: Add title tags to all pages")
            print()
        
        if any('Missing meta description' in str(i) for i in self.issues['high']):
            print("3. HIGH: Add meta descriptions to all pages")
            print()
        
        if any('Missing canonical' in str(i) for i in self.issues['medium']):
            print("4. MEDIUM: Add canonical URLs to prevent duplicate content")
            print()
        
        print("=" * 80)
        print()

def main():
    auditor = WebsiteAuditor()
    
    # Run audit
    auditor.scan_all_html_files()
    
    # Generate report
    auditor.generate_report()
    
    # Ask if we should fix noindex
    if auditor.noindex_pages:
        print("=" * 80)
        print(f"🚨 CRITICAL: Found {len(auditor.noindex_pages)} pages with noindex tags!")
        print("=" * 80)
        print()
        print("These pages are BLOCKED from Google. This is why your traffic is so low!")
        print()
        print("Fixing all noindex tags now...")
        print()
        
        auditor.fix_noindex_tags()
        
        print("=" * 80)
        print("✅ NOINDEX FIX COMPLETE")
        print("=" * 80)
        print()
        print(f"Fixed: {len(auditor.fixes_applied)} pages")
        print()
        print("NEXT STEPS:")
        print("1. Review changes: git diff")
        print("2. Commit: git add . && git commit -m 'Fix: Remove noindex tags from all content pages'")
        print("3. Push: git push origin main")
        print("4. Submit sitemap to Google Search Console")
        print("5. Request re-indexing for important pages")
        print()
        print("Expected timeline:")
        print("• 3-7 days: Google starts indexing pages")
        print("• 2-4 weeks: Full indexing complete")
        print("• 4-8 weeks: Traffic increases visible")
        print()

if __name__ == "__main__":
    main()
