#!/usr/bin/env python3
#
# Generates an HTML file for previewing all styles defined in a CSS file
#
# dependencies: cssutils
# USAGE:
#     css_preview_generator.py style.css > preview.html
import html
import io
import re
import sys

import cssutils

image_placeholder = "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='150' viewBox='0 0 300 150'%3E%3Crect fill='yellow' width='300' height='150'/%3E%3Ctext fill='rgba(0,0,0,0.5)' x='50%25' y='50%25' text-anchor='middle'%3E300×150%3C/text%3E%3C/svg%3E"


def render(s, out):
    if out and not out.closed:
        return print(s, end='', file=out)
    else:
        if out and out.closed:
            sys.stderr.write('‼️‼️‼️‼️OUTPUT STREAM CLOSED!\n')
        print(s, flush=True)


def down_the_rabbit_hole(chunks, full_selector, out=None):
    if len(chunks):
        chunk = chunks.pop(0)
        render_open_tag(chunk, out)
        down_the_rabbit_hole(chunks, full_selector, out)
        render_close_tag(chunk, out)
    else:
        render(full_selector, out)


prefix_map = {
    '.': 'class',
    '#': 'id'
}


def extract_class_id(defn, extracted_attrs=''):
    try:
        for prefix in prefix_map.keys():
            if prefix in defn:
                items = defn.split(prefix)
                value = ' '.join(items[1:])
                # return a tuple of (tagname, 'class="bla blu"') or (tagname, 'id="abc"')
                tag = items[0]
                if any(suffix in tag for suffix in prefix_map.keys()):
                    return extract_class_id(tag, f'{prefix_map[prefix]}="{value}"')
                else:
                    return items[0], f'{extracted_attrs} {prefix_map[prefix]}="{value}"'
    except Exception as e:
        sys.stderr.write(str(e) + "\n")

    return defn, ''


def render_open_tag(definition, out):
    if definition.startswith(('.', '#')):
        _, class_or_id = extract_class_id(definition)
        render(f'<div {class_or_id}>', out)
    else:
        if definition == 'a' or definition.startswith(('a.', 'a#')):
            tag, class_or_id = extract_class_id(definition)
            render(f'''<a {class_or_id} href="#">''', out)

        elif definition == 'img' or definition.startswith(('img.','img#')):
            render(f'<img src="{image_placeholder}" alt="[image]">', out)
        else:
            tag, class_or_id = extract_class_id(definition)
            render(f'<{tag} {class_or_id}>', out)


def render_close_tag(definition, out):
    if definition.startswith(('.', '#')):
        render('</div>', out)
    else:
        if definition == 'a' or definition.startswith(('a.', 'a#')):
            render(f'⚓️ {definition}</a>', out)
        else:
            tag, _ = extract_class_id(definition)
            render(f'</{tag}>', out)


if __name__ == '__main__':

    if len(sys.argv) == 1 or sys.argv[1] in (('-h', '--help')):
        print(f'Usage: {sys.argv[0]} style.css')
        sys.exit(-1)

    already_seen = []
    css_file = sys.argv[1]
    sheet = cssutils.parseFile(css_file)
    print(f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CSS preview: {css_file}</title>
    <link href="{css_file}" rel="stylesheet" type="text/css" />
</head>
<body>
''')
    selectors_requiring_iframe = []
    # build a list of absolute & fixed rules
    for rule in sheet:
        if isinstance(rule, cssutils.css.CSSStyleRule):
            position = getattr(rule.style, 'position', None)

            if position in ('fixed', 'absolute', 'sticky'):
                for single_selector in rule.selectorList:  # type: cssutils.css.Selector
                    selectors_requiring_iframe.append(single_selector.selectorText)

    # deduplicate list
    selectors_requiring_iframe = list(dict.fromkeys(selectors_requiring_iframe))

    for rule in sheet:
        if isinstance(rule, cssutils.css.CSSStyleRule):
            selectors: cssutils.css.SelectorList = getattr(rule, 'selectorList', [])
            full_selectors_text = rule.selectorText
            sys.stderr.write(f'selectors: {full_selectors_text}\n')

            for single_selector in selectors:  # type: cssutils.css.Selector
                if not single_selector or single_selector.selectorText.startswith(('html', 'body')):
                    continue

                #  TODO:  workaround for '~' '*' '+' and '[]' (not supported, ignoring them)
                clean_selector = re.sub('\s*>\s*', ' ', single_selector.selectorText.split(':')[0].split('[')[0]) \
                    .replace('*', '') \
                    .replace('~', '') \
                    .replace('+', '')

                if clean_selector in already_seen:
                    continue
                else:
                    already_seen.append(clean_selector)

                position = getattr(rule.style, 'position', None)

                # if current selector is a child of an absolute/fixed rule then also wrap it in an iframe
                matching_abs_parents = [sel for sel in selectors_requiring_iframe if sel in single_selector.selectorText]

                need_iframe = position in ('fixed', 'absolute', 'sticky') or len(matching_abs_parents)

                out = None
                if need_iframe:
                    print(
                        f'''<iframe width="400" height="300" srcdoc="{html.escape(f'<html><head><link href="{css_file}" rel="stylesheet" type="text/css"/></head><body style="background:azure">')}''',
                        end='')
                    out = io.StringIO()

                down_the_rabbit_hole(clean_selector.split(), full_selectors_text, out)

                if need_iframe:
                    print(html.escape(out.getvalue()), end='')
                    out.close()
                    del out
                    print('"></iframe>')
print('''
</body>
</html>''')
