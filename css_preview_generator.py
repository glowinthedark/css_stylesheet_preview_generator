#!/usr/bin/env python3
#
# Generates an HTML file for previewing all styles defined in a CSS file
#
# dependencies: cssutils
# USAGE:
#     css_preview_generator.py style.css -o preview.html
import html
import io
import sys

import cssutils

image_placeholder = "data:image/svg+xml;charset=UTF-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='150' viewBox='0 0 300 150'%3E%3Crect fill='yellow' width='300' height='150'/%3E%3Ctext fill='rgba(0,0,0,0.5)' x='50%25' y='50%25' text-anchor='middle'%3E300×150%3C/text%3E%3C/svg%3E"


def render(s, out):
    # if isinstance(out, io.StringIO):
    #     terminator = ''
    # else:
    #     terminator = '\n'
    print(s, end='', file=out)


def process_css_definitions(chunks, full_selector, out):
    if len(chunks):
        chunk = chunks.pop(0)
        render_open_tag(chunk, out)
        process_css_definitions(chunks, full_selector, out)
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
        print(e, file=sys.stderr)

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
            if tag.lower() == 'td':
                render(f'<table><thead><tr><th>&#x1F536;&#x1F537;[th]&#x1F537;&#x1F536;</th></thead><tbody><tr><td {class_or_id}>&#x1F539;[td]&#x1F539;<br/>', out)
            else:
                render(f'<{tag} {class_or_id}>', out)


def render_close_tag(definition, out):
    if definition.startswith(('.', '#')):
        render('</div>', out)
    else:
        if definition == 'a' or definition.startswith(('a.', 'a#')):
            render(f'⚓️ {definition}</a>', out)
        else:
            tag, _ = extract_class_id(definition)
            if tag.lower() == 'td':
                render('</td></tr></tbody></table>', out)
            else:
                render(f'</{tag}>', out)


if __name__ == '__main__':

    import argparse

    parser = argparse.ArgumentParser(description='CSS Preview Generator')
    parser.add_argument('css_file',
                        help='CSS stylesheet file name')
    parser.add_argument('--verbose', '-v',
                        help='Verbose output',
                        default=False,
                        action='store_true')
    parser.add_argument('--output-file', '-o',
                        metavar='output',
                        help='HTML preview filename')
    parser.add_argument('--no-frames', '-nf',
                        default=False,
                        action='store_true',
                        help='Do NOT wrap fixed/absolute elements in iframe')

    args = parser.parse_args(sys.argv[1:])

    output_file = open(args.output_file, 'w') or sys.stdout

    already_seen = []

    sheet = cssutils.parseFile(args.css_file)

    print('Generating HTML preview. Please wait...', file=sys.stderr)

    print(f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>CSS preview: {args.css_file}</title>
    <link href="{args.css_file}" rel="stylesheet" type="text/css" />
</head>
<body>
''', file=output_file)

    selectors_requiring_iframe = []
    # build a list of absolute & fixed rules

    if not args.no_frames:
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

            if args.verbose:
                print(f'CSS Rule: {full_selectors_text}', file=sys.stderr)

            for single_selector in selectors:  # type: cssutils.css.Selector

                current_selector_text = single_selector.selectorText
                if not single_selector or current_selector_text.startswith(('html', 'body')):
                    continue

                # 1. convert '>' to space
                # 2.  '~' '*' '+' and '[]' (not supported, ignoring them, convert to space, breaks semantics FIXME)
                for c in '>*~+':
                    if c in current_selector_text:
                        current_selector_text = current_selector_text.replace(c, ' ')

                for c in ':[':
                    if c in current_selector_text:
                        current_selector_text = current_selector_text.split(c)[0]

                if current_selector_text in already_seen:
                    continue
                else:
                    already_seen.append(current_selector_text)

                if '  ' in current_selector_text:
                    current_selector_text = current_selector_text.replace('  ', ' ')

                position = getattr(rule.style, 'position', None)

                need_iframe = False

                if not args.no_frames:
                    # if current selector is a child of an absolute/fixed rule then also wrap it in an iframe
                    matching_abs_parents = [sel for sel in selectors_requiring_iframe if sel in current_selector_text]

                    need_iframe = position in ('fixed', 'absolute', 'sticky') or len(matching_abs_parents)

                    need_table = False

                if need_iframe:
                    print(
                        f'''<iframe style="border:1px dotted #acad9e;" width="400" height="300" srcdoc="{html.escape(f'<html><head><link href="{args.css_file}" rel="stylesheet" type="text/css"/></head><body style="background:#f6f4ee">')}''',
                        end='', file=output_file)

                    out = io.StringIO()
                else:
                    out = output_file

                if args.verbose:
                    print(f'\t{current_selector_text}', file=sys.stderr)
                process_css_definitions(current_selector_text.split(), full_selectors_text, out)

                if need_iframe:
                    print(html.escape(out.getvalue()), end='', file=output_file)
                    print('"></iframe><br/>', file=output_file)
    print('''
    </body>
    </html>''', file=output_file)

    if args.output_file:
        print(f'Wrote HTML to {args.output_file}.', file=sys.stderr)
