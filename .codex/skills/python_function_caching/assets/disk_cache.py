import functools
import inspect
from typing import Any, Optional
from diskcache import Cache


def diskcache_decorator(expire: Optional[float] = None):
    """
    Decorator to cache function results using a diskcache.Cache instance.

    Args:
        expire (Optional[float]): Expiration time for cache entries in seconds.
            If None, cache entries do not expire.

    Returns:
        function: A decorator that caches the output of the decorated function.
            The cache key is based on the function name, positional arguments,
            and sorted keyword arguments. To bypass the cache, pass
            'ignore_cache=True' as a keyword argument.
    """
    # If cache is a str or Path, create a Cache instance
    cache = Cache("~/.cache/project_name")

    def decorator(func):
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        params.append(
            inspect.Parameter(
                "extra_cache_key",
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Any,
            )
        )
        params.append(
            inspect.Parameter(
                "ignore_cache",
                inspect.Parameter.KEYWORD_ONLY,
                default=False,
                annotation=bool,
            )
        )
        wrapper_sig = sig.replace(parameters=params)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            extra_cache_key = kwargs.pop("extra_cache_key", None)
            ignore_cache = kwargs.pop("ignore_cache", False)
            key = (func.__name__, args, tuple(sorted(kwargs.items())), extra_cache_key)
            if not ignore_cache and key in cache:
                return cache[key]
            result = func(*args, **kwargs)
            cache.set(key, result, expire=expire)
            return result

        wrapper.__doc__ = (
            (func.__doc__ or "")
            + "\n\nKwargs:\n    ignore_cache (bool): Bypass cache."
            + "\n    extra_cache_key (Any): Extra key for computing disk hash key. "
            + "\n\nResults of function are cached on disk at ~/.cache/project_name."
        )
        wrapper.__signature__ = wrapper_sig  # type: ignore[attr-defined]
        return wrapper

    return decorator
