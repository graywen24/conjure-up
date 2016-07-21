""" Async Handler
Provides async operations for various api calls and other non-blocking
work.
"""

import asyncio
import logging
from collections import defaultdict

log = logging.getLogger("async")


class ThreadCancelledException(Exception):
    """Exception meaning intentional cancellation"""


ShutdownEvent = asyncio.Event()

_locks = defaultdict(lambda: asyncio.Lock())
DEFAULT_QUEUE = "DEFAULT"

_all_tasks = []


def submit(func, exc_callback, queue_name=DEFAULT_QUEUE):
    task = asyncio.ensure_future(submit_func(func, exc_callback, queue_name))
    _all_tasks.append(task)
    return task


@asyncio.coroutine
def submit_func(func, exc_callback, queue_name):
    with (yield from _locks[queue_name]):

        if ShutdownEvent.is_set():
            return
        try:
            r = func()
            return r
        except Exception as e:
            if exc_callback:
                exc_callback(e)


def submit_shell_cmd(cmd, output_list, queue_name=DEFAULT_QUEUE):
    task = asyncio.ensure_future(submit_shell_coroutine(cmd,
                                                        output_list,
                                                        queue_name))
    _all_tasks.append(task)
    return task


@asyncio.coroutine
def read_lines_from_stream(stream, output_list, tag):
    while True:
        line = yield from stream.readline()
        if not line:
            break
        output_list.append(tag + line.decode())


@asyncio.coroutine
def submit_shell_coroutine(cmd, output_list, queue_name):

    with (yield from _locks[queue_name]):
        if ShutdownEvent.is_set():
            return
        create = asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)

        proc = yield from create

        yield from asyncio.gather(
            read_lines_from_stream(proc.stdout, output_list, '  '),
            read_lines_from_stream(proc.stderr, output_list, '* '))

        yield from proc.wait()
    return proc


def shutdown():
    ShutdownEvent.set()
    for t in _all_tasks:
        t.cancel()


def sleep(s):
    f = asyncio.ensure_future(asyncio.sleep(s))
    _all_tasks.append(f)
    if f.cancelled():
        return
    f.result()
