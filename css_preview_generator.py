#!/usr/bin/env python3
# 
# Generates an HTML file for previewing all styles defined in a CSS file
# 
# dependencies: cssutils
# USAGE:
#     css_preview_generator.py style.css > preview.html

import re
import sys
import cssutils

image_placeholder = "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='150' viewBox='0 0 300 150'%3E%3Crect fill='yellow' width='300' height='150'/%3E%3Ctext fill='rgba(0,0,0,0.5)' x='50%25' y='50%25' text-anchor='middle'%3E300×150%3C/text%3E%3C/svg%3E"


def down_the_rabbit_hole(chunks, full_selector):
    if len(chunks):
        chunk = chunks.pop(0)
        render_open_tag(chunk)
        down_the_rabbit_hole(chunks, full_selector)
        render_close_tag(chunk)
    else:
        print(full_selector)


prefix_map = {
    '.': 'class',
    '#': 'id'
}


def extract_class_id(defn):
    try:
        for prefix in prefix_map.keys():
            if prefix in defn:
                items = defn.split(prefix)
                value = ' '.join(items[1:])
                # returns a tuple of (tagname, 'class="bla"') or (tagname, 'id="abl"')
                return items[0], f'{prefix_map[prefix]}="{value}"'
    except Exception as e:
        print(e)

    return defn, ''


def render_open_tag(definition):
    if definition.startswith(('.', '#')):
        _, class_or_id = extract_class_id(definition)
        print(f'<div {class_or_id}>')
    else:
        if definition == 'a' or definition.startswith(('a.','a#')):
            tag, class_or_id = extract_class_id(definition)
            print(f'''<a {class_or_id} href="#">''')

        elif definition == 'img' or definition.startswith('img.'):
            print(f'<img src="{image_placeholder}" alt="[image]">')
        elif '.' in definition:
            items = definition.split('.')
            tag = items[0]
            classes = ' '.join(items[1:])
            print(f'<{tag} class="{classes}">')
        else:
            tag, class_or_id = extract_class_id(definition)
            print(f'<{tag} {class_or_id}>')


def render_close_tag(definition):
    if definition.startswith(('.', '#')):
        print('</div>')
    else:
        if definition == 'a' or definition.startswith(('a.', 'a#')):
            print(f'⚓️ {definition}</a>')
        else:
            tag, _ = extract_class_id(definition)
            print(f'</{tag}>')


if __name__ == '__main__':
    already_seen = []
    css_file = sys.argv[1]
    sheet = cssutils.parseFile(css_file)
    print(f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title></title>
    <link href="{css_file}" rel="stylesheet" type="text/css" />
</head>
<body>
''')
    for rule in sheet:
        if hasattr(rule, 'selectorList'):
            sys.stderr.write(rule.selectorText + '\n')
            for selector in rule.selectorList:
                if hasattr(rule, 'selectorText'):
                    if selector.selectorText.startswith(('html', 'body')):
                        continue

                    #  FIXME:   dirty workaround for ~ * + (not supported, ignoring them)
                    clean_selector = re.sub('\s*>\s*', ' ', selector.selectorText.split(':')[0].split('[')[0]) \
                        .replace('*', '') \
                        .replace('~', '') \
                        .replace('+', '')

                    if clean_selector in already_seen:
                        continue
                    else:
                        already_seen.append(clean_selector)
                    down_the_rabbit_hole(clean_selector.split(), rule.selectorText)
print('''
</body>
</html>''')
