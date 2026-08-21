# Think Stats 3 — PDF Build

A pre-built PDF of *Think Stats, 3rd Edition* by Allen Downey, with all code cells executed and outputs (tables, charts, math) rendered inline. Each chapter is followed immediately by its solutions.

## Original work

- **Author:** Allen Downey
- **Source:** [AllenDowney/ThinkStats (v3 branch)](https://github.com/AllenDowney/ThinkStats/tree/v3)
- **Published at:** <https://allendowney.github.io/ThinkStats/>
- **License:** [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/)

This repository only redistributes the content in a different format. No modifications were made to the text or code. The same CC BY-NC-SA 4.0 license applies to everything here.

## Build it yourself

Install dependencies:

```sh
pip install -r requirements.txt
```

Generate the PDF:

```sh
python convert_book.py
```

Requires Google Chrome to be installed. Already-processed chapters are cached in `chapters/` so the script can be resumed if interrupted.

### Cache layers

- Delete `chapters/*.pdf` to re-render layout/CSS changes (fast, no re-execution)
- Delete `chapters/*.html` to fully re-execute notebooks (slow)

## See also

- [aautushka/bayes2](https://github.com/aautushka/bayes2) — same treatment for *Think Bayes, 2nd Edition*
