"""Passive advertisement tracker feeding the panel's device table.

In-memory only: HA's bluetooth manager is the source of truth for the current
neighbourhood; we add first/last-seen bookkeeping on top. If persistent
first_seen across restarts ever matters, swap the dict for a
helpers.storage.Store with a debounced save.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.core import HomeAssistant, callback

from .const import CONF_ADDRESS, DOMAIN, HUB_UNIQUE_ID
from .decoders import company_name, humanize_bytes, uuid_name

try:
    # The same clock habluetooth stamps BluetoothServiceInfoBleak.time with.
    from bluetooth_data_tools import monotonic_time_coarse
except ImportError:  # pragma: no cover
    from time import monotonic as monotonic_time_coarse

_LOGGER = logging.getLogger(__name__)

FLUSH_INTERVAL = 2.0  # seconds between pushes to websocket subscribers

# HA only dispatches advertisement callbacks when the payload CONTENT changes
# (identical repeat beacons are short-circuited, and RSSI-only changes don't
# dispatch). HA's internal history does keep fresh timestamps though, so we
# sweep it to keep last_seen/RSSI truthful for stable-payload devices.
SWEEP_INTERVAL = 10.0


def _monotonic_to_epoch(mono: float) -> float:
    return time.time() - (monotonic_time_coarse() - mono)


def _address_type(address: str) -> str:
    """Heuristic BLE address classification from the two MSBs.

    The public/random flag actually lives in the advertising PDU header (not
    exposed by HA), so this is the same best-effort guess tools like nRF
    Connect display: random addresses are tagged in the top bits.
    """
    try:
        first_octet = int(address.split(":")[0], 16)
    except (ValueError, IndexError):
        return "unknown"
    top_bits = (first_octet >> 6) & 0b11
    if top_bits == 0b11:
        return "random static"
    if top_bits == 0b01:
        return "private resolvable (rotates)"
    if top_bits == 0b10:
        return "public"
    return "public or non-resolvable private"


@dataclass
class DeviceRecord:
    """Everything we know about one advertising device."""

    address: str
    name: str | None
    rssi: int | None
    source: str
    connectable: bool
    first_seen: float  # monotonic, converted to epoch on serialize
    last_seen: float
    tx_power: int | None
    adv_count: int = 0
    raw: bytes | None = None
    manufacturer_data: dict[int, bytes] = field(default_factory=dict)
    service_data: dict[str, bytes] = field(default_factory=dict)
    service_uuids: list[str] = field(default_factory=list)


class AdvertisementTracker:
    """Collects all advertisements and pushes debounced updates to subscribers."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._records: dict[str, DeviceRecord] = {}
        self._subscribers: list[Callable[[list[dict]], None]] = []
        self._dirty: set[str] = set()
        self._flush_handle = None
        self._sweep_handle = None
        self._unsub_advertisements: Callable[[], None] | None = None

    @property
    def devices(self) -> dict[str, DeviceRecord]:
        return self._records

    @callback
    def async_start(self) -> None:
        for info in async_discovered_service_info(self._hass, connectable=False):
            self._upsert(info, count=False)
        self._dirty.clear()
        self._sweep_handle = self._hass.loop.call_later(SWEEP_INTERVAL, self._sweep)
        # connectable=False means "don't require the connectable path", i.e.
        # every advertisement from every adapter/proxy — same matcher HA's own
        # bluetooth/subscribe_advertisements API uses. (A None matcher gets
        # rewritten to connectable=True, which sees far fewer dispatches.)
        self._unsub_advertisements = bluetooth.async_register_callback(
            self._hass,
            self._on_advertisement,
            BluetoothCallbackMatcher(connectable=False),
            BluetoothScanningMode.PASSIVE,
        )
        _LOGGER.debug("Tracker started with %d seeded devices", len(self._records))

    @callback
    def async_stop(self) -> None:
        if self._unsub_advertisements is not None:
            self._unsub_advertisements()
            self._unsub_advertisements = None
        if self._flush_handle is not None:
            self._flush_handle.cancel()
            self._flush_handle = None
        if self._sweep_handle is not None:
            self._sweep_handle.cancel()
            self._sweep_handle = None
        self._subscribers.clear()

    @callback
    def async_subscribe(
        self, subscriber: Callable[[list[dict]], None]
    ) -> Callable[[], None]:
        self._subscribers.append(subscriber)

        def _unsubscribe() -> None:
            if subscriber in self._subscribers:
                self._subscribers.remove(subscriber)

        return _unsubscribe

    def snapshot(self) -> list[dict]:
        return [self.serialize(rec) for rec in self._records.values()]

    @callback
    def _on_advertisement(
        self, info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        self._upsert(info)
        self._dirty.add(info.address)
        if self._subscribers and self._flush_handle is None:
            self._flush_handle = self._hass.loop.call_later(
                FLUSH_INTERVAL, self._flush
            )

    @callback
    def _sweep(self) -> None:
        """Refresh last_seen/RSSI from HA's history for stable-payload devices."""
        self._sweep_handle = self._hass.loop.call_later(SWEEP_INTERVAL, self._sweep)
        for info in async_discovered_service_info(self._hass, connectable=False):
            rec = self._records.get(info.address)
            if rec is None:
                self._upsert(info, count=False)
                self._dirty.add(info.address)
            elif info.time > rec.last_seen + 1.0:
                rec.last_seen = info.time
                rec.rssi = info.rssi
                rec.source = info.source
                if info.raw:
                    rec.raw = info.raw
                self._dirty.add(info.address)
        if self._dirty and self._subscribers and self._flush_handle is None:
            self._flush_handle = self._hass.loop.call_later(FLUSH_INTERVAL, self._flush)

    def _upsert(self, info: BluetoothServiceInfoBleak, count: bool = True) -> None:
        rec = self._records.get(info.address)
        if rec is None:
            rec = DeviceRecord(
                address=info.address,
                name=None,
                rssi=None,
                source=info.source,
                connectable=info.connectable,
                first_seen=info.time,
                last_seen=info.time,
                tx_power=None,
            )
            self._records[info.address] = rec
        if count:
            rec.adv_count += 1
        rec.last_seen = info.time
        rec.source = info.source
        rec.rssi = info.rssi
        rec.connectable = rec.connectable or info.connectable
        if info.name and info.name != info.address:
            rec.name = info.name
        if info.tx_power is not None:
            rec.tx_power = info.tx_power
        if info.raw:
            rec.raw = info.raw
        # Merge rather than replace: devices alternate between advertisement
        # frames, and we want the union of everything they've broadcast.
        rec.manufacturer_data.update(info.manufacturer_data)
        rec.service_data.update(info.service_data)
        for uuid in info.service_uuids:
            if uuid not in rec.service_uuids:
                rec.service_uuids.append(uuid)

    @callback
    def _flush(self) -> None:
        self._flush_handle = None
        if not self._dirty:
            return
        changed = [
            self.serialize(self._records[address])
            for address in self._dirty
            if address in self._records
        ]
        self._dirty.clear()
        for subscriber in list(self._subscribers):
            subscriber(changed)

    def serialize(self, rec: DeviceRecord) -> dict:
        return {
            "address": rec.address,
            "address_type": _address_type(rec.address),
            "name": rec.name,
            "rssi": rec.rssi,
            "source": rec.source,
            "connectable": rec.connectable,
            "first_seen": _monotonic_to_epoch(rec.first_seen),
            "last_seen": _monotonic_to_epoch(rec.last_seen),
            "adv_count": rec.adv_count,
            "tx_power": rec.tx_power,
            "raw": rec.raw.hex() if rec.raw else None,
            "manufacturer_name": (
                company_name(next(iter(rec.manufacturer_data)))
                if rec.manufacturer_data
                else None
            ),
            "manufacturer_data": [
                {
                    "company_id": cid,
                    "company_name": company_name(cid),
                    **humanize_bytes(raw),
                }
                for cid, raw in rec.manufacturer_data.items()
            ],
            "service_uuids": [
                {"uuid": uuid, "name": uuid_name(uuid)} for uuid in rec.service_uuids
            ],
            "service_data": [
                {"uuid": uuid, "name": uuid_name(uuid), **humanize_bytes(raw)}
                for uuid, raw in rec.service_data.items()
            ],
            "added_entry_id": self._added_entry_id(rec.address),
        }

    def _added_entry_id(self, address: str) -> str | None:
        for entry in self._hass.config_entries.async_entries(DOMAIN):
            if entry.unique_id == HUB_UNIQUE_ID:
                continue
            if entry.data.get(CONF_ADDRESS) == address:
                return entry.entry_id
        return None
