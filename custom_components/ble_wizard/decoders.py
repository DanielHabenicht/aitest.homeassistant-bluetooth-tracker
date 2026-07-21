"""Decoding BLE payloads into human-readable values.

Two layers:
- KNOWN_CHARACTERISTICS: standard Bluetooth SIG characteristics we can decode
  fully, with proper HA units and device classes.
- Generic decoders (utf8 / uint_le / sint_le / hex) for everything else; the
  user picks one in the panel when adding an unknown characteristic.

This module is deliberately free of connection logic so it can be exercised
with plain bytes.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from bleak.uuids import uuidstr_to_str
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfPressure,
    UnitOfTemperature,
)

from .const import (
    CONF_CHAR_DECODER,
    CONF_CHAR_HANDLE,
    CONF_CHAR_NAME,
    CONF_CHAR_UUID,
)

try:
    # Private bleak module; guard so a future bleak refactor degrades gracefully.
    from bleak.backends._manufacturers import MANUFACTURERS
except ImportError:  # pragma: no cover
    MANUFACTURERS: dict[int, str] = {}

_LOGGER = logging.getLogger(__name__)

BASE_UUID_SUFFIX = "-0000-1000-8000-00805f9b34fb"

DECODER_KNOWN = "known"
DECODER_UTF8 = "utf8"
DECODER_UINT_LE = "uint_le"
DECODER_SINT_LE = "sint_le"
DECODER_HEX = "hex"
GENERIC_DECODER_KINDS = (DECODER_UTF8, DECODER_UINT_LE, DECODER_SINT_LE, DECODER_HEX)


def sig_uuid(short: int) -> str:
    """Expand a 16-bit SIG UUID to its 128-bit string form."""
    return f"0000{short:04x}{BASE_UUID_SUFFIX}"


def _uint_le(raw: bytes) -> int:
    if not 1 <= len(raw) <= 8:
        raise ValueError(f"cannot decode {len(raw)} bytes as integer")
    return int.from_bytes(raw, "little", signed=False)


def _sint_le(raw: bytes) -> int:
    if not 1 <= len(raw) <= 8:
        raise ValueError(f"cannot decode {len(raw)} bytes as integer")
    return int.from_bytes(raw, "little", signed=True)


def _utf8(raw: bytes) -> str:
    return raw.decode("utf-8").rstrip("\x00")


@dataclass(frozen=True)
class KnownChar:
    """A standard characteristic we can decode with proper HA metadata."""

    name: str
    decode: Callable[[bytes], int | float | str]
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = SensorStateClass.MEASUREMENT
    entity_category: EntityCategory | None = None


KNOWN_CHARACTERISTICS: dict[str, KnownChar] = {
    sig_uuid(0x2A19): KnownChar(
        name="Battery Level",
        decode=lambda raw: raw[0],
        unit=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    sig_uuid(0x2A6E): KnownChar(
        name="Temperature",
        # GATT Temperature: sint16, 0.01 degC resolution
        decode=lambda raw: int.from_bytes(raw[0:2], "little", signed=True) / 100,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
    ),
    sig_uuid(0x2A6F): KnownChar(
        name="Humidity",
        # GATT Humidity: uint16, 0.01 %RH resolution
        decode=lambda raw: int.from_bytes(raw[0:2], "little") / 100,
        unit=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
    ),
    sig_uuid(0x2A6D): KnownChar(
        name="Pressure",
        # GATT Pressure: uint32, 0.1 Pa resolution -> hPa
        decode=lambda raw: int.from_bytes(raw[0:4], "little") / 1000,
        unit=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.PRESSURE,
    ),
    sig_uuid(0x2A07): KnownChar(
        name="Tx Power Level",
        decode=lambda raw: int.from_bytes(raw[0:1], "little", signed=True),
        unit=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    sig_uuid(0x2A00): KnownChar(
        name="Device Name",
        decode=_utf8,
        state_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    sig_uuid(0x2A24): KnownChar(
        name="Model Number",
        decode=_utf8,
        state_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    sig_uuid(0x2A25): KnownChar(
        name="Serial Number",
        decode=_utf8,
        state_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    sig_uuid(0x2A26): KnownChar(
        name="Firmware Revision",
        decode=_utf8,
        state_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    sig_uuid(0x2A27): KnownChar(
        name="Hardware Revision",
        decode=_utf8,
        state_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    sig_uuid(0x2A28): KnownChar(
        name="Software Revision",
        decode=_utf8,
        state_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    sig_uuid(0x2A29): KnownChar(
        name="Manufacturer Name",
        decode=_utf8,
        state_class=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}

GENERIC_DECODERS: dict[str, Callable[[bytes], int | str]] = {
    DECODER_UTF8: _utf8,
    DECODER_UINT_LE: _uint_le,
    DECODER_SINT_LE: _sint_le,
    DECODER_HEX: lambda raw: raw.hex(),
}


def char_key(uuid: str, handle: int | None) -> str:
    """Stable key for a characteristic within a device (uuid may repeat)."""
    return f"{uuid}_{handle if handle is not None else 'x'}"


def company_name(company_id: int) -> str:
    return MANUFACTURERS.get(company_id, f"Unknown (0x{company_id:04X})")


def uuid_name(uuid: str) -> str:
    """Human name for a service/characteristic UUID, short form as fallback."""
    name = uuidstr_to_str(uuid)
    if name and name != "Unknown":
        return name
    if uuid.endswith(BASE_UUID_SUFFIX):
        return f"0x{uuid[4:8].upper()}"
    return uuid


def _printable_utf8(raw: bytes) -> str | None:
    """Decode as utf-8 only if the result is entirely printable text."""
    try:
        text = _utf8(raw)
    except UnicodeDecodeError:
        return None
    if text and all(c.isprintable() or c.isspace() for c in text):
        return text
    return None


def ascii_preview(raw: bytes) -> str:
    """Byte-for-byte ASCII with '.' placeholders, like a hex-dump gutter."""
    return "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in raw)


def humanize_bytes(raw: bytes) -> dict[str, str | int | None]:
    """The standard multi-view rendering of an opaque payload for the UI."""
    small = 1 <= len(raw) <= 8
    return {
        "hex": raw.hex(),
        "ascii": ascii_preview(raw),
        "uint_le": _uint_le(raw) if small else None,
        "sint_le": _sint_le(raw) if small else None,
    }


def decode_candidates(raw: bytes) -> list[dict[str, str | int]]:
    """Plausible interpretations of an unknown value, best first."""
    candidates: list[dict[str, str | int]] = []
    if (text := _printable_utf8(raw)) is not None:
        candidates.append({"kind": DECODER_UTF8, "value": text})
    if 1 <= len(raw) <= 8:
        candidates.append({"kind": DECODER_UINT_LE, "value": _uint_le(raw)})
        if raw[-1] & 0x80:  # sint differs from uint only when the sign bit is set
            candidates.append({"kind": DECODER_SINT_LE, "value": _sint_le(raw)})
    candidates.append({"kind": DECODER_HEX, "value": raw.hex()})
    return candidates


def suggested_decoder(uuid: str, raw: bytes) -> str:
    if uuid in KNOWN_CHARACTERISTICS:
        return DECODER_KNOWN
    if _printable_utf8(raw) is not None:
        return DECODER_UTF8
    if 1 <= len(raw) <= 8:
        return DECODER_UINT_LE
    return DECODER_HEX


def decode_value(decoder: str, uuid: str, raw: bytes) -> int | float | str | None:
    """Decode a polled value; None (never an exception) on any failure."""
    try:
        if decoder == DECODER_KNOWN:
            known = KNOWN_CHARACTERISTICS.get(uuid)
            if known is None:
                _LOGGER.debug("No known decoder for %s", uuid)
                return None
            return known.decode(raw)
        return GENERIC_DECODERS[decoder](raw)
    except (ValueError, IndexError, KeyError, UnicodeDecodeError) as err:
        _LOGGER.debug("Failed to decode %s via %s: %s", uuid, decoder, err)
        return None


def build_entity_description(cfg: dict) -> SensorEntityDescription:
    """SensorEntityDescription for a stored CharConfig (metadata never stored)."""
    uuid = cfg[CONF_CHAR_UUID]
    key = char_key(uuid, cfg.get(CONF_CHAR_HANDLE))
    if cfg[CONF_CHAR_DECODER] == DECODER_KNOWN and uuid in KNOWN_CHARACTERISTICS:
        known = KNOWN_CHARACTERISTICS[uuid]
        return SensorEntityDescription(
            key=key,
            name=known.name,
            native_unit_of_measurement=known.unit,
            device_class=known.device_class,
            state_class=known.state_class,
            entity_category=known.entity_category,
        )
    return SensorEntityDescription(
        key=key,
        name=cfg.get(CONF_CHAR_NAME) or uuid_name(uuid),
    )
