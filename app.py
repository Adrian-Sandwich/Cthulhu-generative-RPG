#!/usr/bin/env python3
"""
Cthulhu Lighthouse Game - Web Interface

Application factory. The routes live in web/*_routes.py as blueprints; this
module wires them to a GameContext and serves the two page routes that are not
API surface.
"""

import logging
import os
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from web.context import EXTENSION_KEY, GameContext
from web import admin_routes, api_routes, game_routes, page_routes
from core.postgres_store import StorageUnavailable
from core.timing import TimingMiddleware, logger as timing_logger, log_record

logger = logging.getLogger(__name__)


def create_app(config=None):
    """Build a fresh Flask app instance.

    Per-application state lives on the GameContext stored in app.extensions, so
    tests and workers each get an isolated copy — several apps can coexist in
    one process without sharing a session registry.
    """
    config = config or {}
    app = Flask(__name__)
    context = GameContext(config)
    app.extensions[EXTENSION_KEY] = context

    @app.errorhandler(StorageUnavailable)
    def storage_unavailable(error):
        return jsonify({'error': 'Game storage is temporarily unavailable. Please retry.'}), 503

    app.config['SECRET_KEY'] = context.load_secret_key()
    # Cookie hardening: Lax blocks cross-site POST CSRF (e.g. a forged /reset
    # that would wipe a player's autosave) while still allowing normal top-level
    # nav.
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    # Frontend is served by this same app; CORS only needed for external
    # origins, configurable via comma-separated CORS_ORIGINS env var. When CORS
    # is enabled we must allow credentials so the session cookie rides
    # cross-origin.
    _cors_origins = [o for o in
                     (config.get('CORS_ORIGINS')
                      or os.environ.get('CORS_ORIGINS', '')).split(',') if o]
    if _cors_origins:
        CORS(app, origins=_cors_origins, supports_credentials=True)

    app.register_blueprint(game_routes.bp)
    app.register_blueprint(api_routes.bp)
    app.register_blueprint(admin_routes.bp)
    app.register_blueprint(page_routes.bp)

    if config.get('REQUEST_TIMING', os.environ.get('REQUEST_TIMING', '0') == '1'):
        @app.after_request
        def timing_route(response):
            request.environ['cthulhu.route'] = request.url_rule.rule if request.url_rule else '<unmatched>'
            return response

        if not timing_logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            timing_logger.addHandler(handler)
        timing_logger.setLevel(logging.INFO)
        timing_logger.propagate = False
        app.wsgi_app = TimingMiddleware(app.wsgi_app, config.get('TIMING_SINK', log_record))

    return app



# Keep the module-level app instance so WSGI servers (gunicorn, etc.) can use
# ``app:app`` without any configuration changes.
app = create_app()


if __name__ == '__main__':
    logging.basicConfig(level=os.environ.get('LOG_LEVEL', 'INFO'))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'
    port = int(os.environ.get('PORT', '5000'))
    host = os.environ.get('HOST', '127.0.0.1')
    # Never run the Werkzeug debugger (RCE) on a non-loopback bind.
    if debug and host != '127.0.0.1':
        logger.warning("Refusing FLASK_DEBUG=1 with non-loopback HOST — forcing debug off.")
        debug = False
    create_app().run(debug=debug, host=host, port=port)
