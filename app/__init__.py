
from app.config import load_configurations, configure_logging
from .views import webhook_blueprint
from quart import Quart

def create_app():
    app = Quart(__name__)
    # Load configurations and logging settings
    load_configurations(app)
    configure_logging()
    # Import and register blueprints, if any
    app.register_blueprint(webhook_blueprint)
    return app
