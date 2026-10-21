#!/usr/bin/env python3
"""Builds the website into _site/ from content/ (text), media/ (uploads),
templates/ (page layouts) and assets/ (styles and scripts).

Run:  python3 build.py            (BASE_PATH env var sets a sub-folder, e.g. /repo)
"""
import os, re, shutil, datetime, glob, hashlib
import yaml, markdown
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, '_site')
BASE = os.environ.get('BASE_PATH', '').rstrip('/')

NAV = [
    {'key': 'home', 'label': 'Home', 'url': '/'},
    {'key': 'about', 'label': 'About', 'url': '/about.html'},
    {'key': 'teaching', 'label': 'Teaching', 'url': '/teaching.html'},
    {'key': 'research', 'label': 'Research', 'url': '/research.html'},
    {'key': 'design', 'label': 'Design', 'url': '/design.html'},
    {'key': 'art', 'label': 'Art & Craft', 'url': '/art.html'},
    {'key': 'tools', 'label': 'Tools', 'url': '/tools.html'},
]
# Project categories: key -> label on the filter button and on the small tag
CATEGORIES = {
    'uiux': {'chip': 'UI/UX', 'pill': 'UI/UX'},
    'data': {'chip': 'Data Visualization', 'pill': 'Data Viz'},
    'logo': {'chip': 'Logo Design', 'pill': 'Logo'},
    'pub': {'chip': 'Publication Design', 'pill': 'Publication'},
    'event': {'chip': 'Event Branding', 'pill': 'Event Branding'},
}


def load_yaml(name):
    with open(os.path.join(ROOT, 'content', name), encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def load_projects():
    items = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'content', 'projects', '*.md'))):
        text = open(path, encoding='utf-8').read()
        m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', text, re.S)
        data = (yaml.safe_load(m.group(1)) if m else {}) or {}
        body = (m.group(2) if m else text).strip()
        if body and not data.get('description'):
            data['description'] = body
        if data.get('hidden'):
            continue
        slug = os.path.splitext(os.path.basename(path))[0]
        data['slug'] = slug
        data['url'] = f'design-{slug}.html'
        data['categories'] = [c for c in (data.get('categories') or []) if c]
        data['sections'] = data.get('sections') or []
        data['images'] = data.get('images') or []
        images = [i for i in data['images'] if i and i.get('image')]
        data['card_image'] = data.get('thumbnail') or (images[0]['image'] if images else '')
        items.append(data)
    items.sort(key=lambda p: (p.get('order') if p.get('order') is not None else 999, p['title'].lower()))
    return items


def md(text):
    if not text:
        return Markup('')
    return Markup(markdown.markdown(str(text), extensions=['sane_lists']))


def mdinline(text):
    html = str(md(text)).strip()
    if html.startswith('<p>') and html.endswith('</p>') and html.count('<p>') == 1:
        html = html[3:-4]
    return Markup(html)


def url(path):
    if not path:
        return ''
    path = str(path)
    if re.match(r'^[a-z]+:', path) or path.startswith('//'):
        return path
    if not path.startswith('/'):
        path = '/' + path
    return BASE + path


def main():
    site = load_yaml('site.yml')
    show = bool(site.get('show_prompts', True))
    projects = load_projects()
    for p in projects:
        p['sections_visible'] = [s for s in p['sections'] if s and s.get('heading') and (s.get('text') or (show and s.get('prompt')))]
        p['images_visible'] = [i for i in p['images'] if i and (i.get('image') or show)]

    # Art collage on phones is two columns: a half-width work left alone on its row goes full width
    art = load_yaml('art.yml')
    works = [w for w in (art.get('works') or []) if w and w.get('title')]
    for i, w in enumerate(works):
        w['size'] = w.get('size') or 'medium'
    col = 0
    for i, w in enumerate(works):
        full = w['size'] in ('large', 'wide')
        if full:
            col = 0
            continue
        nxt = works[i + 1] if i + 1 < len(works) else None
        if col == 0 and (nxt is None or nxt['size'] in ('large', 'wide')):
            w['phone_full'] = True
            continue
        col = (col + 1) % 2
    art['works'] = works

    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, 'templates')),
                      autoescape=select_autoescape(['html']), trim_blocks=False, lstrip_blocks=False)
    env.filters.update(md=md, mdinline=mdinline, url=url)
    # Version tags on the stylesheet and script, so browsers fetch new copies after every change
    def ver(name):
        with open(os.path.join(ROOT, 'assets', name), 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    asset_v = {'css': ver('styles.css'), 'js': ver('script.js')}
    common = dict(site=site, asset_v=asset_v, nav=NAV, base=BASE, categories=CATEGORIES,
                  year=datetime.date.today().year,
                  home=load_yaml('home.yml'), about=load_yaml('about.yml'),
                  teaching=load_yaml('teaching.yml'), research=load_yaml('research.yml'),
                  art=art, tools=load_yaml('tools.yml'),
                  projects=projects,
                  used_categories={c for p in projects for c in p['categories']})

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    def render(template, outfile, **ctx):
        html = env.get_template(template).render(**common, **ctx)
        with open(os.path.join(OUT, outfile), 'w', encoding='utf-8') as f:
            f.write(html)

    name = site.get('name', '')
    render('index.html', 'index.html', section='home', page_title=name,
           description=f'Portfolio of {name}: typography scholar, visual and interaction designer.')
    render('about.html', 'about.html', section='about', page_title='About',
           description=f'Education, work experience and awards of {name}.')
    render('teaching.html', 'teaching.html', section='teaching', page_title='Teaching',
           description=f'Teaching experience of {name}.')
    render('research.html', 'research.html', section='research', page_title='Research',
           description=f'Journal publications, conference publications and presentations of {name}.')
    render('design.html', 'design.html', section='design', page_title='Design Projects',
           description=f'UI/UX, data visualization, logo and publication design projects by {name}.')
    render('art.html', 'art.html', section='art', page_title='Art & Craft',
           description=f'Art and craft work by {name}.')
    render('tools.html', 'tools.html', section='tools', page_title='Tools',
           description=f'Web tools developed by {name} for design, research and other purposes.')
    render('404.html', '404.html', section='', page_title='Page not found',
           description='This page could not be found.', noindex=True)
    n = len(projects)
    for i, p in enumerate(projects):
        desc = re.sub(r'\s+', ' ', str(p.get('description') or '')).strip()
        render('project.html', p['url'], section='design', page_title=p['title'],
               description=(desc[:155] + '…') if len(desc) > 156 else desc,
               p=p, prev=projects[(i - 1) % n], next=projects[(i + 1) % n])

    shutil.copytree(os.path.join(ROOT, 'assets'), os.path.join(OUT, 'assets'))
    if os.path.isdir(os.path.join(ROOT, 'media')):
        shutil.copytree(os.path.join(ROOT, 'media'), os.path.join(OUT, 'media'),
                        ignore=shutil.ignore_patterns('.gitkeep'))
    if os.path.exists(os.path.join(ROOT, 'CNAME')):
        shutil.copy(os.path.join(ROOT, 'CNAME'), OUT)
    open(os.path.join(OUT, '.nojekyll'), 'w').close()
    print(f'Built {8 + n} pages into _site/')


if __name__ == '__main__':
    main()
