from zeno.core.permissions import Decision, PermissionEngine


def test_default_confirm_requires_confirmation():
    engine = PermissionEngine()
    assert engine.check("some.tool", confirmed=False) is False
    assert engine.check("some.tool", confirmed=True) is True


def test_explicit_allow_never_needs_confirmation():
    engine = PermissionEngine()
    engine.set_rule("safe.tool", Decision.ALLOW)
    assert engine.check("safe.tool", confirmed=False) is True


def test_explicit_deny_always_blocks():
    engine = PermissionEngine()
    engine.set_rule("dangerous.tool", Decision.DENY)
    assert engine.check("dangerous.tool", confirmed=True) is False


def test_default_can_be_overridden_to_allow():
    engine = PermissionEngine(default=Decision.ALLOW)
    assert engine.check("anything", confirmed=False) is True
