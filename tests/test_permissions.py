from zeno.core.permissions import Decision, PermissionEngine


def test_confirm_requires_explicit_true() -> None:
    engine = PermissionEngine(default=Decision.CONFIRM)

    assert engine.check("notes.create") is False
    assert engine.check("notes.create", confirmed=True) is True


def test_deny_rule_is_never_auto_overridden() -> None:
    engine = PermissionEngine(default=Decision.ALLOW)
    engine.set_rule("device.control", Decision.DENY)

    assert engine.check("device.control") is False
    assert engine.check("device.control", confirmed=True) is False


def test_specific_rule_takes_precedence_over_default() -> None:
    engine = PermissionEngine(default=Decision.ALLOW)
    engine.set_rule("notes.create", Decision.CONFIRM)

    assert engine.check("notes.create") is False
    assert engine.check("notes.create", confirmed=True) is True
