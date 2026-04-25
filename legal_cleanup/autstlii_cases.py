import pywikibot
from pywikibot import pagegenerators
import re
from urllib.parse import urlparse

SITE = pywikibot.Site("en", "wikipedia")
SUMMARY = "Converting {{cite web}} to {{cite AustLII}} for applicable Australian cases."

def parse_template_params(template_text):
    content = template_text.strip()[2:-2]
    params = {}
    parts = re.split(r'\|(?![^\[]*\]\])', content)
    
    for part in parts[1:]:
        if '=' in part:
            k, v = part.split('=', 1)
            params[k.strip().lower()] = v.strip()
    return params

def get_austlii_data(params):
    url = params.get('url', '')
    if not url:
        return None
        
    path_parts = urlparse(url).path.split('/')
    
    try:
        if 'cases' in path_parts:
            court = path_parts[4]
            year = path_parts[5]
            num = path_parts[6].replace('.html', '')
            
            raw_title = params.get('title', '')
            litigants = re.sub(r"''+", "", raw_title)
            # cite web titles are often italicised for the case name, so we strip the wikimarkup
            litigants = litigants.split('[')[0].split('(')[0].strip()
            
            return {
                'court': court,
                'year': year,
                'num': num,
                'litigants': litigants
            }
    except IndexError:
        return None
    return None

def process_page(page):
    text = page.text
    pattern = r"\{\{cite web\s*\|[^}]*url=https?://www\.austlii\.edu\.au/au/cases/[^}]*\}\}"
    
    new_text = text
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    for old_template in matches:
        params = parse_template_params(old_template)
        data = get_austlii_data(params)
        
        if data:
            new_bits = [
                f"litigants={data['litigants']}",
                f"court={data['court']}",
                f"year={data['year']}",
                f"num={data['num']}"
            ]
            
            if 'access-date' in params:
                new_bits.append(f"access-date={params['access-date']}")
            elif 'accessdate' in params:
                new_bits.append(f"access-date={params['accessdate']}")
                
            if 'page' in params:
                new_bits.append(f"pinpoint={params['page']}")
            elif 'at' in params:
                new_bits.append(f"pinpoint={params['at']}")
            
            if 'ref' in params:
                new_bits.append(f"ref={params['ref']}")

            new_template = "{{cite AustLII |" + " |".join(new_bits) + "}}"
            new_text = new_text.replace(old_template, new_template)
            
    if text != new_text:
        pywikibot.showDiff(text, new_text)
        return new_text
    return None

def main():
    search_query = 'insource:/austlii\.edu\.au\/au\/cases\/cth\/HCA/'
    gen = pagegenerators.SearchPageGenerator(search_query, site=SITE)
    
    for page in pagegenerators.PreloadingGenerator(gen, groupsize=50):
        print(f"\nChecking: {page.title()}")
        updated_text = process_page(page)
        
        if updated_text:
            choice = pywikibot.input_choice("Save changes?", [('Yes', 'y'), ('No', 'n'), ('Quit', 'q')], default='n')
            if choice == 'q':
                break
            if choice == 'y':
                page.text = updated_text
                #page.save(SUMMARY)

if __name__ == "__main__":
    main()