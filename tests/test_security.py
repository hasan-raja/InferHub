from app.core.config import Settings
from app.core.security import Role, default_rpm_for_role, generate_api_key, hash_api_key, role_has_permission


def test_api_key_hash_is_stable_and_secret_dependent():
    settings = Settings(api_key_pepper="pepper-one")
    other_settings = Settings(api_key_pepper="pepper-two")

    first = hash_api_key("ih_test", settings)
    second = hash_api_key("ih_test", settings)
    other = hash_api_key("ih_test", other_settings)

    assert first == second
    assert first != "ih_test"
    assert first != other


def test_generated_api_key_shape():
    settings = Settings(api_key_pepper="pepper")
    generated = generate_api_key(settings)

    assert generated.raw_key.startswith("ih_")
    assert generated.prefix == generated.raw_key[:12]
    assert generated.key_hash == hash_api_key(generated.raw_key, settings)


def test_role_permissions():
    assert role_has_permission(Role.ADMIN, "models:write")
    assert role_has_permission(Role.ENTERPRISE, "inference:invoke")
    assert not role_has_permission(Role.FREE, "models:write")


def test_default_rate_limits_by_role():
    settings = Settings(default_free_rpm=1, default_enterprise_rpm=2, default_admin_rpm=3)

    assert default_rpm_for_role(Role.FREE, settings) == 1
    assert default_rpm_for_role(Role.ENTERPRISE, settings) == 2
    assert default_rpm_for_role(Role.ADMIN, settings) == 3

