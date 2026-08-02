# Yuxuan Zhao — Personal Website

A dependency-free, responsive academic website for [yuxuan-zhao.com](https://www.yuxuan-zhao.com/).

## Preview locally

Run any static file server from this folder. For example:

```powershell
python -m http.server 4173
```

Then visit `http://localhost:4173`.

## Deploy

The site is plain HTML, CSS, and JavaScript. It can be deployed to GitHub Pages, Netlify, Vercel, Cloudflare Pages, or any static host without a build command.

The `CNAME` file connects the GitHub Pages deployment to the custom domain.

## Refresh notebook pages

The notebook library contains static reading copies of selected public notebooks. The render step downloads the current files from their source repositories but does not execute any code:

```powershell
python -m pip install -r requirements-notebooks.txt
python scripts/render_notebooks.py
```

Website pushes deploy the committed static notebook pages without re-rendering them. The `Refresh notebooks and deploy Pages` workflow can still be started manually when a refresh from the public source repositories is wanted; automatic scheduled refreshes are currently disabled.
