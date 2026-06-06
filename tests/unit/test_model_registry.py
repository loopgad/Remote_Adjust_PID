"""Tests for ModelRegistry — model registration, querying, and version management."""

import pytest
from param_id_gui.core.model_registry import (
    FidelityLevel,
    Domain,
    Port,
    ModelMetadata,
    ModelRegistry,
)


# ── Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def registry():
    """Return a fresh ModelRegistry instance."""
    return ModelRegistry()


@pytest.fixture
def sample_port():
    """Return a sample input port."""
    return Port(name="v_dc", unit="V", dtype="float64", range_min=0, range_max=600, description="DC bus voltage")


@pytest.fixture
def motor_metadata():
    """Return sample PMSM motor metadata."""
    return ModelMetadata(
        model_id="mdl://motor/pmsm/dq/v1",
        model_name="PMSM DQ Model",
        domain=Domain.MOTOR,
        fidelity=FidelityLevel.L2_LUMPED,
        input_ports=[
            Port(name="v_d", unit="V", description="d-axis voltage"),
            Port(name="v_q", unit="V", description="q-axis voltage"),
        ],
        output_ports=[
            Port(name="i_d", unit="A", description="d-axis current"),
            Port(name="i_q", unit="A", description="q-axis current"),
            Port(name="torque", unit="N.m", description="electromagnetic torque"),
        ],
        sim_step_ns=10000,
        is_realtime_capable=True,
        version="1.0.0",
        author="test",
    )


@pytest.fixture
def power_metadata():
    """Return sample buck converter metadata."""
    return ModelMetadata(
        model_id="mdl://power/buck/v1",
        model_name="Buck Converter Model",
        domain=Domain.POWER,
        fidelity=FidelityLevel.L2_LUMPED,
        input_ports=[
            Port(name="v_in", unit="V", description="input voltage"),
            Port(name="duty", unit="", description="duty cycle"),
        ],
        output_ports=[
            Port(name="v_out", unit="V", description="output voltage"),
        ],
        version="2.0.0",
    )


@pytest.fixture
def controller_metadata():
    """Return sample FOC controller metadata."""
    return ModelMetadata(
        model_id="mdl://controller/foc/v1",
        model_name="FOC Controller",
        domain=Domain.CONTROLLER,
        fidelity=FidelityLevel.L1_EMPIRICAL,
        dependencies=["mdl://motor/pmsm/dq/v1"],
        version="1.0.0",
    )


# ── Enum Tests ────────────────────────────────────────────────

def test_fidelity_level_enum():
    """Test FidelityLevel enum values."""
    assert FidelityLevel.L0_STUB.value == 0
    assert FidelityLevel.L1_EMPIRICAL.value == 1
    assert FidelityLevel.L2_LUMPED.value == 2
    assert FidelityLevel.L3_PHYSICS.value == 3
    assert FidelityLevel.L4_HIGH_FIDELITY.value == 4


def test_domain_enum():
    """Test Domain enum values."""
    assert Domain.POWER.value == "power"
    assert Domain.MOTOR.value == "motor"
    assert Domain.SENSOR.value == "sensor"
    assert Domain.CONTROLLER.value == "controller"
    assert Domain.THERMAL.value == "thermal"


# ── Port Tests ────────────────────────────────────────────────

def test_port_creation(sample_port):
    """Test Port creation with all fields."""
    assert sample_port.name == "v_dc"
    assert sample_port.unit == "V"
    assert sample_port.dtype == "float64"
    assert sample_port.range_min == 0
    assert sample_port.range_max == 600


def test_port_defaults():
    """Test Port default values."""
    port = Port(name="test", unit="A")
    assert port.dtype == "float64"
    assert port.range_min == -float("inf")
    assert port.range_max == float("inf")
    assert port.description == ""


def test_port_invalid_range_raises():
    """Port with range_min > range_max should raise ValueError."""
    with pytest.raises(ValueError):
        Port(name="test", unit="", range_min=10.0, range_max=5.0)


# ── ModelMetadata Tests ───────────────────────────────────────

def test_metadata_creation(motor_metadata):
    """Test ModelMetadata creation."""
    assert motor_metadata.model_id == "mdl://motor/pmsm/dq/v1"
    assert motor_metadata.model_name == "PMSM DQ Model"
    assert motor_metadata.domain == Domain.MOTOR
    assert motor_metadata.fidelity == FidelityLevel.L2_LUMPED


def test_metadata_ports(motor_metadata):
    """Test ModelMetadata port lists."""
    assert len(motor_metadata.input_ports) == 2
    assert len(motor_metadata.output_ports) == 3
    assert motor_metadata.input_ports[0].name == "v_d"
    assert motor_metadata.output_ports[0].name == "i_d"


def test_metadata_to_dict(motor_metadata):
    """Test ModelMetadata serialization."""
    d = motor_metadata.to_dict()
    assert d["model_id"] == "mdl://motor/pmsm/dq/v1"
    assert d["model_name"] == "PMSM DQ Model"
    assert d["domain"] == "motor"
    assert d["fidelity"] == 2
    assert d["version"] == "1.0.0"


# ── Registration Tests ───────────────────────────────────────

def test_register_model(registry, motor_metadata):
    """Test basic model registration."""
    model = {"type": "pmsm", "params": {"Rs": 0.5}}
    registry.register(model, motor_metadata)
    assert registry.model_count == 1


def test_register_duplicate_raises(registry, motor_metadata):
    """Test duplicate registration raises ValueError."""
    model = {"type": "pmsm"}
    registry.register(model, motor_metadata)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(model, motor_metadata)


def test_register_multiple_models(registry, motor_metadata, power_metadata):
    """Test registering multiple models."""
    registry.register({"id": "m1"}, motor_metadata)
    registry.register({"id": "m2"}, power_metadata)
    assert registry.model_count == 2


# ── Query Tests ───────────────────────────────────────────────

def test_get_model(registry, motor_metadata):
    """Test getting model by ID."""
    model = {"type": "pmsm"}
    registry.register(model, motor_metadata)
    result = registry.get("mdl://motor/pmsm/dq/v1")
    assert result is model


def test_get_nonexistent_raises(registry):
    """Test getting nonexistent model raises KeyError."""
    with pytest.raises(KeyError, match="Model not found"):
        registry.get("nonexistent")


def test_get_metadata(registry, motor_metadata):
    """Test getting metadata by ID."""
    registry.register({"type": "pmsm"}, motor_metadata)
    meta = registry.get_metadata("mdl://motor/pmsm/dq/v1")
    assert meta.model_name == "PMSM DQ Model"
    assert meta.domain == Domain.MOTOR


def test_get_metadata_nonexistent_raises(registry):
    """Test getting nonexistent metadata raises KeyError."""
    with pytest.raises(KeyError, match="metadata not found"):
        registry.get_metadata("nonexistent")


# ── Domain Query Tests ────────────────────────────────────────

def test_list_by_domain(registry, motor_metadata, power_metadata, controller_metadata):
    """Test filtering models by domain."""
    registry.register({"id": "m1"}, motor_metadata)
    registry.register({"id": "m2"}, power_metadata)
    registry.register({"id": "m3"}, controller_metadata)

    motor_models = registry.list_by_domain(Domain.MOTOR)
    assert len(motor_models) == 1
    assert "mdl://motor/pmsm/dq/v1" in motor_models

    power_models = registry.list_by_domain(Domain.POWER)
    assert len(power_models) == 1
    assert "mdl://power/buck/v1" in power_models


def test_list_by_domain_empty(registry, motor_metadata):
    """Test domain query with no matches."""
    registry.register({"id": "m1"}, motor_metadata)
    result = registry.list_by_domain(Domain.THERMAL)
    assert len(result) == 0


# ── Fidelity Query Tests ──────────────────────────────────────

def test_list_by_fidelity(registry, motor_metadata, power_metadata, controller_metadata):
    """Test filtering models by fidelity level."""
    registry.register({"id": "m1"}, motor_metadata)
    registry.register({"id": "m2"}, power_metadata)
    registry.register({"id": "m3"}, controller_metadata)

    lumped = registry.list_by_fidelity(FidelityLevel.L2_LUMPED)
    assert len(lumped) == 2  # motor + power

    empirical = registry.list_by_fidelity(FidelityLevel.L1_EMPIRICAL)
    assert len(empirical) == 1  # controller


def test_list_by_fidelity_empty(registry, motor_metadata):
    """Test fidelity query with no matches."""
    registry.register({"id": "m1"}, motor_metadata)
    result = registry.list_by_fidelity(FidelityLevel.L4_HIGH_FIDELITY)
    assert len(result) == 0


# ── List All / List Models Tests ──────────────────────────────

def test_list_all(registry, motor_metadata, power_metadata):
    """Test listing all metadata."""
    registry.register({"id": "m1"}, motor_metadata)
    registry.register({"id": "m2"}, power_metadata)
    all_meta = registry.list_all()
    assert len(all_meta) == 2
    assert "mdl://motor/pmsm/dq/v1" in all_meta
    assert "mdl://power/buck/v1" in all_meta


def test_list_models(registry, motor_metadata, power_metadata):
    """Test listing all model IDs."""
    registry.register({"id": "m1"}, motor_metadata)
    registry.register({"id": "m2"}, power_metadata)
    ids = registry.list_models()
    assert len(ids) == 2
    assert "mdl://motor/pmsm/dq/v1" in ids


def test_model_count_empty(registry):
    """Test model count on empty registry."""
    assert registry.model_count == 0


# ── Dependency Validation Tests ───────────────────────────────

def test_validate_dependencies_satisfied(registry, motor_metadata, controller_metadata):
    """Test dependency validation when all deps are met."""
    registry.register({"id": "m1"}, motor_metadata)
    registry.register({"id": "m2"}, controller_metadata)
    missing = registry.validate_dependencies()
    assert len(missing) == 0


def test_validate_dependencies_missing(registry, controller_metadata):
    """Test dependency validation when deps are missing."""
    registry.register({"id": "m2"}, controller_metadata)
    missing = registry.validate_dependencies()
    assert len(missing) == 1
    assert "mdl://motor/pmsm/dq/v1" in missing[0]


def test_validate_dependencies_empty(registry):
    """Test dependency validation on empty registry."""
    missing = registry.validate_dependencies()
    assert len(missing) == 0


# ── Unregister Tests ──────────────────────────────────────────

def test_unregister_model(registry, motor_metadata):
    """Test unregistering a model."""
    registry.register({"id": "m1"}, motor_metadata)
    assert registry.model_count == 1
    registry.unregister("mdl://motor/pmsm/dq/v1")
    assert registry.model_count == 0


def test_unregister_nonexistent_no_error(registry):
    """Test unregistering a nonexistent model does not raise."""
    registry.unregister("nonexistent")  # Should not raise


# ── Version Management Tests ──────────────────────────────────

def test_version_tracking():
    """Test model version is correctly stored."""
    meta_v1 = ModelMetadata(
        model_id="mdl://power/buck/v1",
        model_name="Buck v1",
        domain=Domain.POWER,
        fidelity=FidelityLevel.L2_LUMPED,
        version="1.0.0",
    )
    meta_v2 = ModelMetadata(
        model_id="mdl://power/buck/v2",
        model_name="Buck v2",
        domain=Domain.POWER,
        fidelity=FidelityLevel.L2_LUMPED,
        version="2.0.0",
    )
    assert meta_v1.version == "1.0.0"
    assert meta_v2.version == "2.0.0"


def test_version_in_dict():
    """Test version appears in serialized dict."""
    meta = ModelMetadata(
        model_id="mdl://test/v1",
        model_name="Test",
        domain=Domain.MOTOR,
        fidelity=FidelityLevel.L0_STUB,
        version="3.1.0",
    )
    d = meta.to_dict()
    assert d["version"] == "3.1.0"


def test_register_multiple_versions():
    """Test registering multiple versions of same logical model."""
    registry = ModelRegistry()

    meta_v1 = ModelMetadata(
        model_id="mdl://motor/pmsm/dq/v1",
        model_name="PMSM DQ v1",
        domain=Domain.MOTOR,
        fidelity=FidelityLevel.L2_LUMPED,
        version="1.0.0",
    )
    meta_v2 = ModelMetadata(
        model_id="mdl://motor/pmsm/dq/v2",
        model_name="PMSM DQ v2",
        domain=Domain.MOTOR,
        fidelity=FidelityLevel.L3_PHYSICS,
        version="2.0.0",
    )

    registry.register({"ver": 1}, meta_v1)
    registry.register({"ver": 2}, meta_v2)
    assert registry.model_count == 2

    # Both accessible by their unique IDs
    assert registry.get_metadata("mdl://motor/pmsm/dq/v1").version == "1.0.0"
    assert registry.get_metadata("mdl://motor/pmsm/dq/v2").version == "2.0.0"

    # v2 has higher fidelity
    v2_meta = registry.get_metadata("mdl://motor/pmsm/dq/v2")
    assert v2_meta.fidelity == FidelityLevel.L3_PHYSICS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
