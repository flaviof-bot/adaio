#!/usr/bin/env python
"""Filtering decisions for Adafruit IO publishes."""

import time

from ada import const


_NUMERIC_VALUE = "number"
_STRING_VALUE = "string"
_REPR_VALUE = "repr"


def feed_key(feed_id, group_id=None):
    if group_id:
        return "{}.{}".format(group_id.replace("_", "-"), feed_id)
    return feed_id


def _normalize_value(value):
    try:
        return (_NUMERIC_VALUE, float(value))
    except (TypeError, ValueError):
        pass
    try:
        return (_STRING_VALUE, str(value))
    except Exception:
        return (_REPR_VALUE, repr(value))


class PublishFilter(object):
    def __init__(self, denylist=None, max_age_secs=None, dedup_exempt=None, clock=None):
        self.denylist = frozenset(const.AIO_FEED_DENYLIST if denylist is None else denylist)
        if max_age_secs is None:
            max_age_secs = const.AIO_PUBLISH_DEDUP_MAX_AGE_SECS
        self.max_age_secs = max_age_secs
        self.dedup_exempt = frozenset(
            const.AIO_FEED_DEDUP_EXEMPT if dedup_exempt is None else dedup_exempt
        )
        self.clock = time.monotonic if clock is None else clock
        self._published = {}
        self.denied_count = 0
        self.suppressed_count = 0
        self.published_count = 0

    @property
    def counters(self):
        return {
            "denied": self.denied_count,
            "suppressed": self.suppressed_count,
            "published": self.published_count,
        }

    def is_denied(self, key):
        return key in self.denylist

    def should_publish(self, key, value, now=None):
        if key in self.dedup_exempt:
            return True
        published = self._published.get(key)
        if published is None:
            return True
        last_value, last_published = published
        if _normalize_value(value) != last_value:
            return True
        if now is None:
            now = self.clock()
        return now - last_published >= self.max_age_secs

    def record_published(self, key, value, now=None):
        if now is None:
            now = self.clock()
        self._published[key] = (_normalize_value(value), now)
        self.published_count += 1

    def record_denied(self):
        self.denied_count += 1

    def record_suppressed(self):
        self.suppressed_count += 1
