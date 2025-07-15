import logging
from .protocol import validate_beckn_payload, handle_on_search, handle_confirm, handle_on_confirm

logger = logging.getLogger(__name__)

def stub_on_search(payload: dict):
    validated = validate_beckn_payload(payload)
    logger.info(f"Processed on_search: {validated}")
    return handle_on_search(validated)

def stub_confirm(payload: dict):
    validated = validate_beckn_payload(payload)
    logger.info(f"Processed confirm: {validated}")
    return handle_confirm(validated)

def stub_on_confirm(payload: dict):
    validated = validate_beckn_payload(payload)
    logger.info(f"Processed on_confirm: {validated}")
    return handle_on_confirm(validated)

# Documentation:
# To extend for full Beckn integration:
# 1. Expand BecknContext and BecknPayload models to match full UEI/Beckn schemas.
# 2. Implement real logic in protocol.py handlers (e.g., integrate with workflow).
# 3. Add authentication, signing, and registry lookups as per Beckn protocol.
