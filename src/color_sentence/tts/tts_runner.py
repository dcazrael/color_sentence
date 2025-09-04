from __future__ import annotations

"""
Lightweight TTS runner: a single background thread with a FIFO queue.
Engine enqueues sentences; worker calls the synchronous ITTS backend.
"""

from dataclasses import dataclass
from queue import Queue, Full, Empty
from threading import Event, Thread
from typing import Protocol

from color_sentence.config.types import ITTS


class ITTSRunner(Protocol):
    """Queue-based, non-blocking TTS executor."""
    def ensure_started(self) -> None: ...
    def enqueue(self, text: str) -> None: ...
    def shutdown(self) -> None: ...


@dataclass
class TtsRunner(ITTSRunner):
    """
    Single-threaded speech runner that calls a blocking ITTS in the background.
    """
    backend: ITTS
    max_queue: int = 32
    _queue: Queue[str] | None = None
    _thread: Thread | None = None
    _stop: Event | None = None

    def ensure_started(self) -> None:
        if self._thread is not None:
            return
        q: Queue[str] = Queue(self.max_queue)
        stop: Event = Event()
        t: Thread = Thread(target=self._loop, args=(q, stop), daemon=True)
        self._queue = q
        self._stop = stop
        t.start()
        self._thread = t

    def enqueue(self, text: str) -> None:
        self.ensure_started()
        assert self._queue is not None
        try:
            self._queue.put_nowait(text)
        except Full:
            try:
                _ = self._queue.get_nowait()
            except Empty:
                pass
            self._queue.put_nowait(text)

    def shutdown(self) -> None:
        if self._stop is not None:
            self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=0.5)
        self._queue = None
        self._thread = None
        self._stop = None


    def _loop(self, q: Queue[str], stop: Event) -> None:
        try:
            self.backend.warmup()
        except RuntimeError:
            pass

        while not stop.is_set():
            try:
                text: str = q.get(timeout=0.1)
            except Empty:
                continue
            try:
                self.backend.speak(text)
            except RuntimeError:
                pass
