from zeno.core.permissions import Decision, PermissionEngine


def test_wildcard_rule_applies_to_unmatched_tools():
    engine = PermissionEngine(default=Decision.ALLOW)
    engine.set_rule("*", Decision.DENY)
    assert engine.check("unknown.tool", confirmed=True) is False


def test_exact_rule_overrides_wildcard():
    engine = PermissionEngine(default=Decision.DENY)
    engine.set_rule("*", Decision.CONFIRM)
    engine.set_rule("safe.tool", Decision.ALLOW)
    assert engine.check("safe.tool") is True
    assert engine.check("other.tool") is False
