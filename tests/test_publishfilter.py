import unittest

from ada.publishfilter import PublishFilter
from ada.publishfilter import feed_key


class FakeClock(object):
    def __init__(self, now=0):
        self.now = now

    def __call__(self):
        return self.now


class PublishFilterTest(unittest.TestCase):
    def make_filter(self, **kwargs):
        kwargs.setdefault("denylist", frozenset())
        kwargs.setdefault("dedup_exempt", frozenset())
        kwargs.setdefault("max_age_secs", 3600)
        kwargs.setdefault("clock", FakeClock())
        return PublishFilter(**kwargs)

    def test_denylisted_key_is_denied(self):
        publish_filter = self.make_filter(denylist=frozenset(["group.feed"]))

        self.assertTrue(publish_filter.is_denied("group.feed"))
        self.assertFalse(publish_filter.is_denied("group.feed-other"))

    def test_first_value_for_feed_publishes(self):
        publish_filter = self.make_filter()

        self.assertTrue(publish_filter.should_publish("group.feed", "value"))

    def test_identical_value_inside_window_is_suppressed(self):
        clock = FakeClock(0)
        publish_filter = self.make_filter(clock=clock)
        publish_filter.record_published("group.feed", "value")
        clock.now = 1800

        self.assertFalse(publish_filter.should_publish("group.feed", "value"))

    def test_identical_value_after_window_publishes(self):
        clock = FakeClock(0)
        publish_filter = self.make_filter(clock=clock)
        publish_filter.record_published("group.feed", "value")
        clock.now = 3600

        self.assertTrue(publish_filter.should_publish("group.feed", "value"))

    def test_changed_value_publishes_immediately(self):
        clock = FakeClock(0)
        publish_filter = self.make_filter(clock=clock)
        publish_filter.record_published("group.feed", "old")
        clock.now = 1

        self.assertTrue(publish_filter.should_publish("group.feed", "new"))

    def test_suppression_does_not_extend_window(self):
        clock = FakeClock(0)
        publish_filter = self.make_filter(clock=clock)
        publish_filter.record_published("group.feed", "value")
        clock.now = 1800
        self.assertFalse(publish_filter.should_publish("group.feed", "value"))
        publish_filter.record_suppressed()
        clock.now = 3601

        self.assertTrue(publish_filter.should_publish("group.feed", "value"))

    def test_numeric_values_compare_numerically(self):
        clock = FakeClock(0)
        publish_filter = self.make_filter(clock=clock)
        publish_filter.record_published("group.feed", 1)
        clock.now = 1

        self.assertFalse(publish_filter.should_publish("group.feed", "1"))
        self.assertFalse(publish_filter.should_publish("group.feed", 1.0))
        self.assertTrue(publish_filter.should_publish("group.feed", "on"))

    def test_two_feeds_keep_independent_state(self):
        clock = FakeClock(0)
        publish_filter = self.make_filter(clock=clock)
        publish_filter.record_published("group.feed1", "same")
        clock.now = 1

        self.assertFalse(publish_filter.should_publish("group.feed1", "same"))
        self.assertTrue(publish_filter.should_publish("group.feed2", "same"))

    def test_feed_key(self):
        self.assertEqual("feed", feed_key("feed"))
        self.assertEqual("group.feed", feed_key("feed", "group"))
        self.assertEqual("some-group.feed", feed_key("feed", "some_group"))

    def test_exempt_feed_publishes_every_time(self):
        clock = FakeClock(0)
        publish_filter = self.make_filter(
            clock=clock, dedup_exempt=frozenset(["group.feed"])
        )
        publish_filter.record_published("group.feed", "value")
        clock.now = 1

        self.assertTrue(publish_filter.should_publish("group.feed", "value"))


if __name__ == "__main__":
    unittest.main()
