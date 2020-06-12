# CSS Preview generator

Generate an HTML file for visualizing all styles defined in a CSS stylesheet.

## Usage

```bash
python3 css_stylesheet_preview_generator.py stylesheet.css -o preview.html

## verbose mode
python3 css_stylesheet_preview_generator.py stylesheet.css -v -o preview.html
```

If not output file is specified then HTML is written to stdout. Debug info goes to stderr.
