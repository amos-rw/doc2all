import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()

# Only a running server reaches this file (tests and commands do not), so the deletion timer starts here.
from files import timer  # noqa: E402

timer.start()
