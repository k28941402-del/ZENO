from zeno.core.events import EventBus


def test_publish_calls_subscribed_listener():
    bus = EventBus()
    received = []
    bus.subscribe("ping", lambda e: received.append(e.payload))
    bus.publish("ping", value=42)
    assert received == [{"value": 42}]


def test_wildcard_listener_receives_all_events():
    bus = EventBus()
    received = []
    bus.subscribe("*", lambda e: received.append(e.name))
    bus.publish("a")
    bus.publish("b")
    assert received == ["a", "b"]


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    received = []
    listener = lambda e: received.append(e.name)
    bus.subscribe("x", listener)
    bus.unsubscribe("x", listener)
    bus.publish("x")
    assert received == []


def test_history_filters_by_name():
    bus = EventBus()
    bus.publish("a")
    bus.publish("b")
    bus.publish("a")
    assert len(bus.history("a")) == 2
    assert len(bus.history()) == 3
