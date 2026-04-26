import logging
import os
import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

_handlers: dict[str, list[Callable[..., Coroutine]]] = defaultdict(list)

EVENTS_FAIL_FAST = os.environ.get("EVENTS_FAIL_FAST", "").lower() in {"1", "true", "yes", "on"}
EVENTS_RETRY_ATTEMPTS = max(1, int(os.environ.get("EVENTS_RETRY_ATTEMPTS", "3")))
EVENTS_RETRY_BACKOFF_MS = max(0, int(os.environ.get("EVENTS_RETRY_BACKOFF_MS", "50")))


@dataclass
class PendingEvent:
    name: str
    kwargs: dict[str, Any] = field(default_factory=dict)

    def __init__(self, name: str, **kwargs: Any):
        self.name = name
        self.kwargs = kwargs


def on(event_name: str):
    def decorator(fn: Callable[..., Coroutine]):
        _handlers[event_name].append(fn)
        return fn
    return decorator


async def emit(event_name: str, **kwargs: Any):
    handlers = _handlers.get(event_name, [])
    if not handlers:
        return

    async def _run(handler: Callable[..., Coroutine]) -> None:
        last_exc: Exception | None = None
        for attempt in range(1, EVENTS_RETRY_ATTEMPTS + 1):
            try:
                await handler(**kwargs)
                return
            except Exception as e:
                last_exc = e
                logger.exception(
                    "Error in event handler (event=%s, handler=%s, attempt=%s/%s, kwargs=%s)",
                    event_name,
                    getattr(handler, "__name__", repr(handler)),
                    attempt,
                    EVENTS_RETRY_ATTEMPTS,
                    kwargs,
                )
                if attempt < EVENTS_RETRY_ATTEMPTS and EVENTS_RETRY_BACKOFF_MS > 0:
                    await asyncio.sleep((EVENTS_RETRY_BACKOFF_MS / 1000.0) * (2 ** (attempt - 1)))
        if last_exc is not None and EVENTS_FAIL_FAST:
            raise last_exc

    await asyncio.gather(*[_run(h) for h in handlers])


async def emit_pending(events: list[PendingEvent]):
    await asyncio.gather(*[emit(e.name, **e.kwargs) for e in events])


EVENT_STEP_COMPLETED = "step_completed"
EVENT_STEP_SKIPPED = "step_skipped"
EVENT_SKIPPED_STEP_COMPLETED = "skipped_step_completed"
EVENT_GOAL_CREATED = "goal_created"
EVENT_GOAL_COMPLETED = "goal_completed"
EVENT_GOAL_FROZEN = "goal_frozen"
EVENT_GOAL_UNFROZEN = "goal_unfrozen"
EVENT_DEPOSIT_MADE = "deposit_made"
EVENT_ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
