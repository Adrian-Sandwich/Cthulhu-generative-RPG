#!/usr/bin/env python3
"""
The page shell and its generated assets — everything a browser loads directly
rather than calling as an API.
"""

import logging

from flask import Blueprint, Response, current_app, render_template, send_from_directory
from xml.sax.saxutils import escape

from web.context import ctx

logger = logging.getLogger(__name__)

bp = Blueprint("pages", __name__)


@bp.route('/images/<path:filename>')
def serve_generated_image(filename):
    """Serve generated location images"""
    return send_from_directory(ctx().images_dir, filename)


@bp.route('/')
def index():
    """Main game interface"""
    site = current_app.config['PUBLIC_SITE_URL']
    return render_template('index.html', site_url=site,
        seo_title='The Lighthouse | Solo Horror RPG with an AI Dungeon Master',
        seo_description='Play a solo cosmic horror RPG in your browser. Explore a haunted lighthouse with an AI Dungeon Master, roll dice, and uncover clues. No download or account needed.')


@bp.route('/robots.txt')
def robots():
    site = current_app.config['PUBLIC_SITE_URL']
    if not site:
        return Response('User-agent: *\nDisallow: /\n', mimetype='text/plain')
    return Response('User-agent: *\nAllow: /\nDisallow: /api/\nDisallow: /admin\n'
                    'Disallow: /images/\nSitemap: ' + site + '/sitemap.xml\n', mimetype='text/plain')


@bp.route('/sitemap.xml')
def sitemap():
    site = current_app.config['PUBLIC_SITE_URL']
    entry = '<url><loc>' + escape(site + '/') + '</loc></url>' if site else ''
    return Response('<?xml version="1.0" encoding="UTF-8"?>\n'
                    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
                    + entry + '</urlset>', mimetype='application/xml')
