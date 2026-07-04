from __future__ import annotations

import logging

from fastapi import APIRouter

router = APIRouter(tags=["chat"])
log = logging.getLogger(__name__)
