import asyncio
import inspect
import pytest_asyncio


@pytest_asyncio.fixture
def aio_benchmark(benchmark):  # Removed 'async' from fixture definition
    """A benchmark fixture that safely executes both async and sync targets

    within the active pytest-asyncio event loop context.
    """
    # Capture the active event loop running the current test
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()

    def _wrapper(
        func,
        *args,
        rounds=None,
        iterations=1,
        **kwargs,
    ):
        if inspect.iscoroutinefunction(func):
            result = None

            def runner():
                nonlocal result
                # Safely run the async target inside the existing test loop
                if loop.is_running():
                    # If the loop is already running, schedule and wait for the coroutine
                    future = asyncio.run_coroutine_threadsafe(
                        func(*args, **kwargs), loop
                    )
                    result = future.result()
                else:
                    # Fallback if the loop isn't actively running
                    result = loop.run_until_complete(func(*args, **kwargs))
                return result

            benchmark.pedantic(
                runner,
                rounds=rounds,
                iterations=iterations,
            )
            return result

        # Fallback for standard synchronous functions
        return benchmark.pedantic(
            func,
            args=args,
            kwargs=kwargs,
            rounds=rounds,
            iterations=iterations,
        )

    yield _wrapper
