# CSS Preview generator

Generate an HTML file for visualizing all styles defined in a CSS stylesheet.

## Dependencies

The script requires the `cssutils` module which can be installed with:

```bash
pip3 install cssutils
```


## Usage

```bash
python3 css_stylesheet_preview_generator.py stylesheet.css -o preview.html

## verbose mode
python3 css_stylesheet_preview_generator.py stylesheet.css -v -o preview.html
```

If no output file is specified then HTML is written to stdout. Debug info goes to stderr.

