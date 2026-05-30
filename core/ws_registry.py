from typing import Any, Callable

_handlers: dict[str, Callable] = {}


def on(action: str):
    def decorator(func: Callable):
        _handlers[action] = func
        return func
    return decorator


async def dispatch(action: str, data: dict, db, user: dict = None) -> Any:
    handler = _handlers.get(action)
    if not handler:
        raise ValueError(f"Unknown action: {action}")

    import inspect
    sig = inspect.signature(handler)
    params = list(sig.parameters.keys())

    if "user" in params:
        return await handler(data, db, user=user)
    return await handler(data, db)
