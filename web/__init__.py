"""Web layer: the Flask blueprints and the per-app context they share.

app.py was a single 810-line module in which create_app held 763 of those lines
and all 16 routes as nested closures. Nothing could see a route from outside —
the code graph reported zero Flask routes, because there were no module-level
view functions to find.

The split is by what a route depends on, not by topic:

    game_bp   9 routes  need a session and its engine
    admin_bp  2 routes  need aggregate state across sessions
    api_bp    3 routes  need nothing

`/` and `/images/<path>` stay in create_app: they are the page shell, not API.

Per-application state still lives per application — GameContext is built by the
factory and stored on ``app.extensions["cthulhu"]``, so two apps in one process
(which the tests rely on) keep separate session registries.
"""
