"""
Global DRF exception handler.

Ensures every unhandled server-side exception returns a clean JSON body
instead of leaking a raw traceback. Wire up in config/base.py:

    REST_FRAMEWORK = {
        'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',
        ...
    }
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    # Let DRF handle its own exceptions first (ValidationError, AuthenticationFailed, etc.)
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception — log it and return a safe 500 body.
        view = context.get('view', 'unknown view')
        logger.error(
            f"Unhandled exception in {view}: {exc}",
            exc_info=True,
        )
        return Response(
            {"error": "An unexpected error occurred. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
