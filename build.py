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


def drop_hidden(value):
    """Remove every list item marked 'hidden: true' (at any depth)."""
    if isinstance(value, dict):
        return {k: drop_hidden(v) for k, v in value.items()}
    if isinstance(value, list):
        return [drop_hidden(v) for v in value if not (isinstance(v, dict) and v.get('hidden'))]
    return value


def load_yaml(name):
    with open(os.path.join(ROOT, 'content', name), encoding='utf-8') as f:
        return drop_hidden(yaml.safe_load(f) or {})


def load_projects():
    items = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'content', 'projects', '*.md'))):
        text = open(path, encoding='utf-8').read()
        m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)$', text, re.S)
        data = drop_hidden((yaml.safe_load(m.group(1)) if m else {}) or {})
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
        if data.get('thumbnail'):
            data['card_image'] = data['thumbnail']
            data['card_position'] = data.get('thumbnail_position') or ''
            data['card_zoom'] = data.get('thumbnail_zoom') or ''
        else:
            first = images[0] if images else {}
            data['card_image'] = first.get('image', '')
            data['card_position'] = first.get('position') or ''
            data['card_zoom'] = first.get('zoom') or ''
        items.append(data)
    items.sort(key=lambda p: (p.get('order') if p.get('order') is not None else 999, p['title'].lower()))
    return items


def image_ratio(path):
    """Width ÷ height of an uploaded image (1.5 if it can't be read)."""
    try:
        from PIL import Image
        with Image.open(os.path.join(ROOT, str(path).lstrip('/'))) as im:
            w, h = im.size
        return round(w / h, 4) if h else 1.5
    except Exception:
        return 1.5


def gallery_rows(shots):
    """Arrange any number of images into rows.
    The first image always gets a row of its own. With an even number of images (4 or more),
    the last one does too. The images in between go in pairs; three portrait images share a row."""
    n = len(shots)
    if n == 0:
        return []
    rows = [shots[:1]]
    last_alone = n % 2 == 0 and n > 2
    middle = shots[1:n - 1] if last_alone else shots[1:]
    i, m = 0, len(middle)
    portrait = lambda k: middle[k]['ratio'] < 1
    while i < m:
        left = m - i
        if left >= 3 and all(portrait(i + k) for k in range(3)) and left - 3 != 1:
            take = 3
        elif left >= 2:
            take = 2
        else:
            take = 1
        rows.append(middle[i:i + take]); i += take
    if last_alone:
        rows.append(shots[-1:])
    return rows


def art_layout(works):
    """Compose the Art & Craft collage from each picture's shape and order.

    Pieces are grouped into rows that cycle through four editorial patterns on a
    12-column grid: a large piece with a smaller one dropped beside it, a staggered
    trio, the mirror of the first, and a centred wide piece. Spans follow each
    picture's proportions, so tall works stay narrow and wide works get room.
    Every piece gets: c (start column), s (span), o (drop from the row top, % of
    its width) for desktop, plus ps/po for the two-column phone layout."""
    def kind(w):
        r = w['ratio']
        return 'wide' if r >= 1.35 else ('tall' if r < 0.85 else 'square')

    def big(w):
        return {'wide': 8, 'square': 6, 'tall': 5}[kind(w)]

    def small(w):
        return {'wide': 5, 'square': 4, 'tall': 4}[kind(w)]

    rows, i, n, step = [], 0, len(works), 0
    while i < n:
        left = n - i
        pattern = ['feature-left', 'trio', 'feature-right', 'trio'][step % 4]
        a = works[i]
        if left == 1:
            s_ = {'wide': 10, 'square': 6, 'tall': 5}[kind(a)]
            rows.append([dict(a, c=(12 - s_) // 2 + 1, s=s_, o=0)]); i += 1
        elif pattern == 'trio' and left >= 3:
            trio = works[i:i + 3]
            spans = [small(w) if kind(w) != 'wide' else 4 for w in trio]
            gap = max(0, min(1, (12 - sum(spans)) // 2))
            cols, c = [], 1
            for sp in spans:
                cols.append(c); c += sp + gap
            shift = 12 - (cols[-1] + spans[-1] - 1)
            cols = [cols[0]] + [x + shift // 2 for x in cols[1:-1]] + [cols[-1] + shift]
            drops = [0, 18, 6]
            rows.append([dict(w, c=cols[k], s=spans[k], o=drops[k]) for k, w in enumerate(trio)]); i += 3
        elif pattern == 'trio' and left == 2 and kind(a) == 'wide' and kind(works[i + 1]) == 'wide':
            rows.append([dict(a, c=1, s=6, o=0), dict(works[i + 1], c=7, s=6, o=14)]); i += 2
        else:
            b = works[i + 1]
            if pattern in ('feature-left', 'trio'):
                L, S = big(a), small(b)
                S = min(S, 11 - L)
                rows.append([dict(a, c=1, s=L, o=0), dict(b, c=13 - S, s=S, o=22)])
            else:
                S, L = small(a), big(b)
                S = min(S, 11 - L)
                rows.append([dict(a, c=1, s=S, o=26), dict(b, c=13 - L, s=L, o=0)])
            i += 2
        step += 1

    # Phone: two columns. Wide pieces take the full width; others pair up, the second dropped.
    flat = [w for row in rows for w in row]
    k = 0
    while k < len(flat):
        w = flat[k]
        if kind(w) == 'wide' or k == len(flat) - 1 or kind(flat[k + 1]) == 'wide':
            w['ps'], w['po'] = 2, 0
            w['pw'] = 100 if kind(w) == 'wide' else 72
            k += 1
        else:
            w['ps'], w['po'], w['pw'] = 1, 0, 100
            flat[k + 1]['ps'], flat[k + 1]['po'], flat[k + 1]['pw'] = 1, 22, 100
            k += 2
    return rows


def optimise_media(folder):
    """Shrink very large photos in the published copy (originals in media/ stay untouched)."""
    try:
        from PIL import Image
    except Exception:
        return
    for dirpath, _, files in os.walk(folder):
        for name in files:
            ext = name.lower().rsplit('.', 1)[-1]
            if ext not in ('jpg', 'jpeg', 'png', 'webp'):
                continue
            path = os.path.join(dirpath, name)
            try:
                with Image.open(path) as im:
                    if max(im.size) <= 2400:
                        continue
                    im.thumbnail((2400, 2400))
                    if ext in ('jpg', 'jpeg'):
                        im.convert('RGB').save(path, quality=84, optimize=True, progressive=True)
                    elif ext == 'png':
                        im.save(path, optimize=True)
                    else:
                        im.save(path, quality=84)
            except Exception:
                pass


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
    # Nothing empty is ever shown: no "To add" reminders, no image placeholders
    site['show_prompts'] = False
    show = False
    projects = load_projects()
    for p in projects:
        p['sections_visible'] = [s for s in p['sections'] if s and s.get('heading') and (s.get('text') or (show and s.get('prompt')))]
        shots = [dict(i, ratio=image_ratio(i['image'])) for i in p['images'] if i and i.get('image')]
        p['gallery_rows'] = gallery_rows(shots)

    # Art collage on phones is two columns: a half-width work left alone on its row goes full width
    art = load_yaml('art.yml')
    works = [w for w in (art.get('works') or []) if w and w.get('image')]
    for w in works:
        w['ratio'] = image_ratio(w['image'])
    art['works'] = works
    art['rows'] = art_layout(works)

    env = Environment(loader=FileSystemLoader(os.path.join(ROOT, 'templates')),
                      autoescape=select_autoescape(['html']), trim_blocks=False, lstrip_blocks=False)
    env.filters.update(md=md, mdinline=mdinline, url=url)
    # Version tags on the stylesheet and script, so browsers fetch new copies after every change
    def ver(name):
        with open(os.path.join(ROOT, 'assets', name), 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:8]
    asset_v = {'css': ver('styles.css'), 'js': ver('script.js')}
    hidden_pages = set(site.get('hidden_pages') or [])
    # A page with nothing to show stays out of the menu until content is added
    tools_data = load_yaml('tools.yml')
    if not works:
        hidden_pages.add('art')
    if not any(tools_data.get(k) for k in ('design', 'research', 'other')):
        hidden_pages.add('tools')
    nav = [n for n in NAV if n['key'] not in hidden_pages]
    common = dict(site=site, asset_v=asset_v, nav=nav, base=BASE, categories=CATEGORIES,
                  year=datetime.date.today().year,
                  home=load_yaml('home.yml'), about=load_yaml('about.yml'),
                  teaching=load_yaml('teaching.yml'), research=load_yaml('research.yml'),
                  art=art, tools=tools_data,
                  projects=projects,
                  used_categories={c for p in projects for c in p['categories']})

    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    def render(template, outfile, **ctx):
        if ctx.get('section') in hidden_pages:
            return
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
        optimise_media(os.path.join(OUT, 'media'))
    # Stand-alone web apps: apps/<name>/ is published as-is at /<name>/
    apps = os.path.join(ROOT, 'apps')
    if os.path.isdir(apps):
        for name in sorted(os.listdir(apps)):
            src = os.path.join(apps, name)
            if os.path.isdir(src):
                shutil.copytree(src, os.path.join(OUT, name))
    if os.path.exists(os.path.join(ROOT, 'CNAME')):
        shutil.copy(os.path.join(ROOT, 'CNAME'), OUT)
    open(os.path.join(OUT, '.nojekyll'), 'w').close()
    print(f"Built {len([f for f in os.listdir(OUT) if f.endswith('.html')])} pages into _site/")


if __name__ == '__main__':
    main()
