import os

# Default to the plugins directory: netraven/worker/jobs/plugins/
DEFAULT_PLUGIN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jobs', 'plugins')
NETRAVEN_PLUGIN_PATH = os.getenv('NETRAVEN_PLUGIN_PATH', DEFAULT_PLUGIN_PATH)
