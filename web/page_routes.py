#!/usr/bin/env python3
"""
The page shell and its generated assets — everything a browser loads directly
rather than calling as an API.
"""

import logging

from flask import Blueprint, render_template, send_from_directory

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
    return render_template('index.html')
