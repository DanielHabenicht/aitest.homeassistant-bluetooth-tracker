/* BLE Wizard panel — self-contained custom element, no build step. */

const DECODER_LABELS = {
  known: "Standard",
  utf8: "Text (UTF-8)",
  uint_le: "Number (unsigned)",
  sint_le: "Number (signed)",
  hex: "Hex string",
};

const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]
  );

const BASE_UUID_SUFFIX = "-0000-1000-8000-00805f9b34fb";

const shortUuid = (uuid) =>
  uuid.endsWith(BASE_UUID_SUFFIX) ? `0x${uuid.slice(4, 8).toUpperCase()}` : uuid;

const hexToBytes = (hex) => {
  const out = [];
  for (let i = 0; i + 1 < hex.length; i += 2) out.push(parseInt(hex.slice(i, i + 2), 16));
  return out;
};

const printableAscii = (byte) =>
  byte >= 0x20 && byte <= 0x7e ? String.fromCharCode(byte) : "·";

const leValue = (bytes) => bytes.reduce((acc, b, i) => acc + b * 2 ** (8 * i), 0);

/* Side-by-side payload viewer: hex bytes with ASCII beneath, and little-endian
   numbers for 2- and 4-byte groups aligned under the bytes they cover. */
const payloadTable = (hex) => {
  if (!hex) return '<span class="dim">(empty)</span>';
  const bytes = hexToBytes(hex);
  const n = bytes.length;
  const hexRow = bytes
    .map((b) => `<td>${b.toString(16).padStart(2, "0")}</td>`)
    .join("");
  const asciiRow = bytes
    .map((b) => `<td class="dim">${esc(printableAscii(b))}</td>`)
    .join("");
  const groupRow = (size) => {
    let cells = "";
    for (let i = 0; i < n; i += size) {
      const group = bytes.slice(i, i + size);
      cells +=
        group.length === size
          ? `<td colspan="${size}" title="0x${group
              .map((b) => b.toString(16).padStart(2, "0"))
              .join("")}">${leValue(group)}</td>`
          : `<td colspan="${group.length}" class="dim">—</td>`;
    }
    return cells;
  };
  let utf8 = null;
  try {
    const text = new TextDecoder("utf-8", { fatal: true })
      .decode(new Uint8Array(bytes))
      .replace(/\x00+$/, "");
    if (text && [...text].every((c) => c >= " " || c === "\n" || c === "\t")) utf8 = text;
  } catch {
    /* not text */
  }
  return `<div class="ptwrap"><table class="pt">
      <tr><th>hex</th>${hexRow}</tr>
      <tr><th>ascii</th>${asciiRow}</tr>
      ${n >= 2 ? `<tr><th>u16 le</th>${groupRow(2)}</tr>` : ""}
      ${n >= 4 ? `<tr><th>u32 le</th>${groupRow(4)}</tr>` : ""}
    </table></div>${
      utf8 ? `<div class="row"><span class="k">utf-8</span><span class="mono">${esc(utf8)}</span></div>` : ""
    }`;
};

/* Bluetooth Assigned Numbers, Generic Access Profile AD types. */
const AD_TYPES = {
  0x01: "Flags",
  0x02: "16-bit Service UUIDs (incomplete)",
  0x03: "16-bit Service UUIDs",
  0x04: "32-bit Service UUIDs (incomplete)",
  0x05: "32-bit Service UUIDs",
  0x06: "128-bit Service UUIDs (incomplete)",
  0x07: "128-bit Service UUIDs",
  0x08: "Shortened Local Name",
  0x09: "Complete Local Name",
  0x0a: "Tx Power Level",
  0x12: "Peripheral Connection Interval Range",
  0x14: "16-bit Solicitation UUIDs",
  0x15: "128-bit Solicitation UUIDs",
  0x16: "Service Data (16-bit UUID)",
  0x19: "Appearance",
  0x1a: "Advertising Interval",
  0x1b: "LE Bluetooth Device Address",
  0x1c: "LE Role",
  0x20: "Service Data (32-bit UUID)",
  0x21: "Service Data (128-bit UUID)",
  0x24: "URI",
  0xff: "Manufacturer Specific Data",
};

const FLAG_BITS = [
  "LE Limited Discoverable",
  "LE General Discoverable",
  "BR/EDR Not Supported",
  "Simultaneous LE + BR/EDR (Controller)",
  "Simultaneous LE + BR/EDR (Host)",
];

/* Parse raw advertisement bytes into AD structures with a short decoded view. */
const parseAdStructures = (hex) => {
  const bytes = hexToBytes(hex);
  const structs = [];
  let i = 0;
  while (i < bytes.length) {
    const len = bytes[i];
    if (!len || i + len >= bytes.length + 1) break;
    const type = bytes[i + 1];
    const data = bytes.slice(i + 2, i + 1 + len);
    structs.push({ type, data });
    i += 1 + len;
  }
  return structs.map(({ type, data }) => {
    const name = AD_TYPES[type] || "Unknown";
    const hexStr = data.map((b) => b.toString(16).padStart(2, "0")).join(" ");
    let decoded = "";
    if (type === 0x08 || type === 0x09) {
      decoded = `“${data.map(printableAscii).join("")}”`;
    } else if (type === 0x0a) {
      const v = data[0] > 127 ? data[0] - 256 : data[0];
      decoded = `${v} dBm`;
    } else if (type === 0x01 && data.length) {
      decoded = FLAG_BITS.filter((_, bit) => data[0] & (1 << bit)).join(", ");
    } else if (type === 0x02 || type === 0x03) {
      const uuids = [];
      for (let j = 0; j + 1 < data.length; j += 2)
        uuids.push(`0x${leValue(data.slice(j, j + 2)).toString(16).padStart(4, "0").toUpperCase()}`);
      decoded = uuids.join(", ");
    } else if (type === 0xff && data.length >= 2) {
      decoded = `company 0x${leValue(data.slice(0, 2)).toString(16).padStart(4, "0").toUpperCase()}`;
    } else if (type === 0x16 && data.length >= 2) {
      decoded = `uuid 0x${leValue(data.slice(0, 2)).toString(16).padStart(4, "0").toUpperCase()}`;
    } else if (type === 0x12 && data.length >= 4) {
      const lo = leValue(data.slice(0, 2)) * 1.25;
      const hi = leValue(data.slice(2, 4)) * 1.25;
      decoded = `${lo}–${hi} ms`;
    } else if (type === 0x19 && data.length >= 2) {
      decoded = `0x${leValue(data.slice(0, 2)).toString(16).padStart(4, "0")}`;
    }
    return { type, name, hexStr, decoded };
  });
};

const fmtCount = (n) => {
  if (n == null) return "—";
  if (n >= 10000) return `${(n / 1000).toFixed(n >= 100000 ? 0 : 1)}k`;
  return String(n);
};

const relTime = (epochSeconds) => {
  if (!epochSeconds) return "—";
  const diff = Date.now() / 1000 - epochSeconds;
  if (diff < 5) return "just now";
  if (diff < 60) return `${Math.round(diff)} s ago`;
  if (diff < 3600) return `${Math.round(diff / 60)} min ago`;
  if (diff < 86400) return `${Math.round(diff / 3600)} h ago`;
  return `${Math.round(diff / 86400)} d ago`;
};

class BleWizardPanel extends HTMLElement {
  constructor() {
    super();
    this._devices = new Map(); // address -> record
    this._probes = new Map(); // address -> {status, result?, error?}
    this._busy = new Set(); // "address|uuid|handle" add/remove in flight
    this._sortKey = "last_seen";
    this._sortAsc = false;
    this._filter = "";
    this._drawer = null; // address currently open in the side panel
    this._subscribed = false;
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._subscribed && hass) {
      this._subscribed = true;
      this._subscribe();
    }
  }

  connectedCallback() {
    if (this._root) return;
    this._root = this.attachShadow({ mode: "open" });
    this._root.innerHTML = `
      <style>
        :host {
          display: block;
          padding: 16px;
          color: var(--primary-text-color);
          background: var(--primary-background-color);
          min-height: 100%;
          box-sizing: border-box;
          font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif);
        }
        h1 { font-size: 20px; font-weight: 400; margin: 4px 0 16px; }
        .toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }
        .toolbar input {
          padding: 8px 12px; border-radius: 4px; min-width: 260px;
          border: 1px solid var(--divider-color);
          background: var(--card-background-color); color: var(--primary-text-color);
        }
        .count { color: var(--secondary-text-color); font-size: 13px; }
        .card {
          background: var(--card-background-color);
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 1px 3px rgba(0,0,0,.2));
          overflow-x: auto;
        }
        table { border-collapse: collapse; width: 100%; font-size: 14px; }
        th, td { text-align: left; padding: 10px 12px; white-space: nowrap; }
        th {
          cursor: pointer; user-select: none; font-weight: 500;
          color: var(--secondary-text-color);
          border-bottom: 1px solid var(--divider-color);
        }
        tbody tr { cursor: pointer; }
        tbody tr:hover { background: var(--secondary-background-color); }
        tbody tr.sel { background: var(--secondary-background-color); }
        td { border-bottom: 1px solid var(--divider-color); }
        tr.group td {
          cursor: default; padding: 8px 12px 4px; font-size: 12px; font-weight: 500;
          text-transform: uppercase; letter-spacing: .06em;
          color: var(--secondary-text-color);
          background: var(--primary-background-color);
        }
        tbody tr.group:hover { background: var(--primary-background-color); }
        .mac { font-family: monospace; font-size: 12px; color: var(--secondary-text-color); }
        .devname { font-weight: 400; }
        .dim { color: var(--secondary-text-color); }
        .badge {
          display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 12px;
          background: var(--primary-color); color: var(--text-primary-color, #fff);
        }
        .chip {
          display: inline-block; padding: 1px 8px; border-radius: 10px; font-size: 12px;
          border: 1px solid var(--divider-color); margin: 1px 2px;
        }
        button {
          border: none; border-radius: 4px; padding: 6px 14px; cursor: pointer;
          background: var(--primary-color); color: var(--text-primary-color, #fff);
          font-size: 13px;
        }
        button[disabled] { opacity: .45; cursor: default; }
        button.warn { background: var(--error-color, #b00020); }
        button.ghost {
          background: transparent; color: var(--primary-text-color);
          border: 1px solid var(--divider-color);
        }
        select {
          padding: 4px 6px; border-radius: 4px;
          border: 1px solid var(--divider-color);
          background: var(--card-background-color); color: var(--primary-text-color);
        }
        .mono { font-family: monospace; font-size: 12.5px; word-break: break-all; }
        .error { color: var(--error-color, #b00020); }
        .spin { display: inline-block; animation: spin 1.2s linear infinite; }
        @keyframes spin { to { transform: rotate(360deg); } }
        .empty { padding: 32px; text-align: center; color: var(--secondary-text-color); }

        /* ---- side drawer ---- */
        .backdrop {
          position: fixed; inset: 0; background: rgba(0,0,0,.32); z-index: 4;
        }
        .drawer {
          position: fixed; top: 0; right: 0; bottom: 0; z-index: 5;
          width: min(480px, 92vw);
          background: var(--card-background-color);
          box-shadow: -4px 0 16px rgba(0,0,0,.3);
          display: flex; flex-direction: column;
        }
        .drawer header {
          display: flex; align-items: center; gap: 8px;
          padding: 14px 16px; border-bottom: 1px solid var(--divider-color);
        }
        .drawer header .t { flex: 1; min-width: 0; }
        .drawer header .t .devname { font-size: 16px; }
        .drawer header .x {
          background: transparent; color: var(--primary-text-color);
          font-size: 20px; padding: 4px 10px;
        }
        .drawer .body { overflow-y: auto; padding: 14px 16px; flex: 1; }
        .grid {
          display: grid; grid-template-columns: auto 1fr; gap: 4px 14px;
          font-size: 13.5px; margin-bottom: 14px;
        }
        .grid .k { color: var(--secondary-text-color); white-space: nowrap; }
        .sect { font-weight: 500; margin: 16px 0 6px; font-size: 13px;
                text-transform: uppercase; letter-spacing: .06em;
                color: var(--secondary-text-color); }
        .ptwrap { overflow-x: auto; margin: 4px 0 8px; }
        table.pt { border-collapse: collapse; font-size: 12px; }
        .pt td, .pt th {
          border: 1px solid var(--divider-color); padding: 2px 6px;
          text-align: center; font-family: monospace; white-space: nowrap;
        }
        .pt th {
          text-align: right; color: var(--secondary-text-color); font-weight: 400;
          font-family: inherit;
        }
        .adname { color: var(--secondary-text-color); font-size: 12px; }
        .row { display: flex; align-items: baseline; gap: 8px; margin: 4px 0; flex-wrap: wrap; }
        .row .k { color: var(--secondary-text-color); font-size: 13px; }
        .char {
          margin: 8px 0; padding: 8px 10px;
          border-left: 3px solid var(--divider-color);
        }
        .char .val { margin: 5px 0; }
        .svc { margin: 12px 0 2px; font-weight: 500; }
      </style>
      <h1>BLE Wizard</h1>
      <div class="toolbar">
        <input id="filter" type="text" placeholder="Filter by name, MAC or manufacturer…">
        <span class="count" id="count"></span>
      </div>
      <div class="card">
        <table>
          <thead><tr id="head"></tr></thead>
          <tbody id="body"><tr><td class="empty">Waiting for advertisements…</td></tr></tbody>
        </table>
      </div>
      <div id="drawerhost"></div>
    `;
    this._root.getElementById("filter").addEventListener("input", (ev) => {
      this._filter = ev.target.value.toLowerCase();
      this._renderTable();
    });
    this._root.getElementById("body").addEventListener("click", (ev) => {
      const row = ev.target.closest("tr[data-address]");
      if (row) this._openDrawer(row.dataset.address);
    });
    this._root.getElementById("head").addEventListener("click", (ev) => {
      const key = ev.target.dataset?.sort;
      if (!key) return;
      if (this._sortKey === key) this._sortAsc = !this._sortAsc;
      else { this._sortKey = key; this._sortAsc = key === "name"; }
      this._renderTable();
    });
    this._root.getElementById("drawerhost").addEventListener("click", (ev) => this._onDrawerClick(ev));
    this._renderTable();
    this._timer = setInterval(() => this._renderTimesOnly(), 5000);
  }

  disconnectedCallback() {
    clearInterval(this._timer);
    if (this._unsub) { this._unsub.then((u) => u()).catch(() => {}); this._unsub = null; }
    this._subscribed = false;
  }

  async _subscribe() {
    this._unsub = this._hass.connection.subscribeMessage(
      (ev) => {
        for (const rec of ev.devices || []) this._devices.set(rec.address, rec);
        this._renderTable();
        if (this._drawer && (ev.devices || []).some((d) => d.address === this._drawer)) {
          this._renderDrawer();
        }
      },
      { type: "ble_wizard/subscribe_advertisements" }
    );
  }

  /* ---------- table ---------- */

  _visibleDevices() {
    let records = [...this._devices.values()];
    if (this._filter) {
      records = records.filter((r) =>
        `${r.name ?? ""} ${r.address} ${r.manufacturer_name ?? ""}`
          .toLowerCase()
          .includes(this._filter)
      );
    }
    const key = this._sortKey;
    const dir = this._sortAsc ? 1 : -1;
    records.sort((a, b) => {
      const va = a[key] ?? (typeof b[key] === "number" ? -Infinity : "");
      const vb = b[key] ?? (typeof a[key] === "number" ? -Infinity : "");
      return va < vb ? -dir : va > vb ? dir : 0;
    });
    return records;
  }

  _renderTable() {
    if (!this._root) return;
    const cols = [
      ["name", "Device"], ["manufacturer_name", "Manufacturer"], ["rssi", "RSSI"],
      ["adv_count", "Seen"], ["first_seen", "First seen"], ["last_seen", "Last seen"],
    ];
    this._root.getElementById("head").innerHTML = cols
      .map(
        ([key, label]) =>
          `<th data-sort="${key}">${label}${
            this._sortKey === key ? (this._sortAsc ? " ▲" : " ▼") : ""
          }</th>`
      )
      .join("");
    const records = this._visibleDevices();
    this._root.getElementById("count").textContent =
      `${records.length} of ${this._devices.size} devices`;
    const body = this._root.getElementById("body");
    if (!records.length) {
      body.innerHTML = `<tr><td class="empty" colspan="6">No devices seen yet.</td></tr>`;
      return;
    }
    // Stable addresses first (you can recognize these tomorrow), then the
    // rotating ones that change identity every ~15 minutes.
    const rotates = (r) => (r.address_type || "").includes("rotates");
    const groups = [
      ["Stable addresses", records.filter((r) => !rotates(r))],
      ["Resolvable private addresses (LE Privacy)", records.filter(rotates)],
    ];
    body.innerHTML = groups
      .filter(([, recs]) => recs.length)
      .map(
        ([label, recs]) =>
          `<tr class="group"><td colspan="6">${label} (${recs.length})</td></tr>` +
          recs.map((rec) => this._deviceRow(rec)).join("")
      )
      .join("");
  }

  _deviceRow(rec) {
    return `
        <tr data-address="${esc(rec.address)}" class="${rec.address === this._drawer ? "sel" : ""}">
          <td>
            <div class="devname">${esc(rec.name) || '<span class="dim">(no name)</span>'}
              ${rec.added_entry_id ? '<span class="badge">added</span>' : ""}</div>
            <div class="mac">${esc(rec.address)}</div>
          </td>
          <td>${esc(rec.manufacturer_name) || '<span class="dim">—</span>'}</td>
          <td>${rec.rssi ?? "—"} dBm</td>
          <td>${fmtCount(rec.adv_count)}</td>
          <td class="rel" data-epoch="${rec.first_seen}">${relTime(rec.first_seen)}</td>
          <td class="rel" data-epoch="${rec.last_seen}">${relTime(rec.last_seen)}</td>
        </tr>`;
  }

  _renderTimesOnly() {
    if (!this._root) return;
    for (const cell of this._root.querySelectorAll(".rel")) {
      cell.textContent = relTime(Number(cell.dataset.epoch));
    }
  }

  /* ---------- drawer ---------- */

  _openDrawer(address) {
    this._drawer = address;
    this._renderTable();
    this._renderDrawer();
  }

  _closeDrawer() {
    this._drawer = null;
    this._root.getElementById("drawerhost").innerHTML = "";
    this._renderTable();
  }

  _renderDrawer() {
    const host = this._root.getElementById("drawerhost");
    const rec = this._devices.get(this._drawer);
    if (!rec) { host.innerHTML = ""; return; }

    const services = rec.service_uuids.length
      ? rec.service_uuids
          .map(
            (s) =>
              `<span class="chip" title="${esc(s.uuid)}">${esc(s.name)}
               <span class="mono">${esc(shortUuid(s.uuid))}</span></span>`
          )
          .join(" ")
      : '<span class="dim">none advertised</span>';

    const mfg = rec.manufacturer_data
      .map(
        (m) => `<div class="row">
            <span class="k">${esc(m.company_name)} (0x${m.company_id.toString(16).padStart(4, "0")})</span>
          </div>${payloadTable(m.hex)}`
      )
      .join("");
    const svcData = rec.service_data
      .map(
        (s) => `<div class="row">
            <span class="k" title="${esc(s.uuid)}">${esc(s.name)}
              <span class="mono">${esc(shortUuid(s.uuid))}</span></span>
          </div>${payloadTable(s.hex)}`
      )
      .join("");
    const rawAd = rec.raw
      ? parseAdStructures(rec.raw)
          .map(
            (st) => `<div class="row">
              <span class="k">0x${st.type.toString(16).padStart(2, "0")} ${esc(st.name)}</span>
              <span class="mono">${esc(st.hexStr)}</span>
              ${st.decoded ? `<span class="adname">${esc(st.decoded)}</span>` : ""}
            </div>`
          )
          .join("")
      : '<span class="dim">not captured by this scanner</span>';

    host.innerHTML = `
      <div class="backdrop" data-act="close"></div>
      <div class="drawer">
        <header>
          <div class="t">
            <div class="devname">${esc(rec.name) || '<span class="dim">(no name)</span>'}
              ${rec.added_entry_id ? '<span class="badge">added</span>' : ""}</div>
            <div class="mac">${esc(rec.address)}</div>
          </div>
          <button class="x" data-act="close" title="Close">✕</button>
        </header>
        <div class="body">
          <div class="grid">
            <span class="k">Manufacturer</span><span>${esc(rec.manufacturer_name) || "—"}</span>
            <span class="k">Address type</span><span>${esc(rec.address_type || "unknown")}</span>
            <span class="k">Connectable</span><span>${rec.connectable ? "yes" : "no"}</span>
            <span class="k">Seen via</span><span class="mono">${esc(rec.source)}</span>
            <span class="k">RSSI</span><span>${rec.rssi ?? "—"} dBm</span>
            <span class="k">Adv. updates</span><span>${fmtCount(rec.adv_count)} since HA start
              <span class="dim">(content changes only — HA dedups identical beacons)</span></span>
            ${rec.tx_power != null ? `<span class="k">Tx power</span><span>${rec.tx_power} dBm</span>` : ""}
            <span class="k">First seen</span><span class="rel" data-epoch="${rec.first_seen}">${relTime(rec.first_seen)}</span>
            <span class="k">Last seen</span><span class="rel" data-epoch="${rec.last_seen}">${relTime(rec.last_seen)}</span>
          </div>

          <div class="sect">Advertised services</div>
          <div>${services}</div>

          ${mfg ? `<div class="sect">Manufacturer data</div>${mfg}` : ""}
          ${svcData ? `<div class="sect">Service data</div>${svcData}` : ""}

          <div class="sect">Raw advertisement</div>
          ${rawAd}

          <div class="sect">GATT database</div>
          ${this._probeSection(rec)}
        </div>
      </div>`;
  }

  _probeSection(rec) {
    const probe = this._probes.get(rec.address);
    if (!probe) {
      return `<button data-act="probe" data-address="${esc(rec.address)}"
          ${rec.connectable ? "" : "disabled title='Device does not accept connections'"}>
          Probe device</button>
        <div class="dim" style="margin-top:4px">
          ${rec.connectable
            ? "Connects once and lists everything the device exposes (can take up to 90 s)."
            : "This device does not accept connections."}
        </div>`;
    }
    if (probe.status === "running") {
      return `<span class="spin">◌</span> Probing… <span class="dim">up to 90 s</span>`;
    }
    if (probe.status === "error") {
      return `<div class="error">Probe failed: ${esc(probe.error)}</div>
        <p><button data-act="probe" data-address="${esc(rec.address)}">Retry</button></p>`;
    }
    return (
      this._probeResult(rec, probe.result) +
      `<p><button class="ghost" data-act="probe" data-address="${esc(rec.address)}">Probe again</button></p>`
    );
  }

  _charValue(v) {
    const known = v.known
      ? `<div><b>${esc(v.known.value)}${v.known.unit ? " " + esc(v.known.unit) : ""}</b>
         <span class="dim">(standard decoding)</span></div>`
      : "";
    return `<div class="val">${known}${payloadTable(v.hex)}</div>`;
  }

  _probeResult(rec, result) {
    return result.services
      .map((svc) => {
        const chars = svc.characteristics
          .map((ch) => {
            const key = `${rec.address}|${ch.uuid}|${ch.handle}`;
            const props = ch.properties
              .map((p) => `<span class="chip">${esc(p)}</span>`)
              .join("");
            let valueHtml = "";
            if (ch.readable && ch.value) {
              valueHtml = ch.value.error
                ? `<div class="val error">read failed: ${esc(ch.value.error)}</div>`
                : this._charValue(ch.value);
            }
            let addHtml = "";
            if (ch.readable && ch.value && !ch.value.error) {
              const options = [
                ...(ch.value.known ? [["known", "Standard"]] : []),
                ...ch.value.candidates.map((c) => [c.kind, DECODER_LABELS[c.kind] || c.kind]),
              ];
              const seen = new Set();
              const opts = options
                .filter(([k]) => !seen.has(k) && seen.add(k))
                .map(
                  ([k, label]) =>
                    `<option value="${k}" ${k === ch.suggested_decoder ? "selected" : ""}>${label}</option>`
                )
                .join("");
              const busy = this._busy.has(key);
              addHtml = ch.added
                ? `<span class="badge">sensor added</span>
                   <button class="warn" data-act="remove" data-address="${esc(rec.address)}"
                     data-uuid="${esc(ch.uuid)}" data-handle="${ch.handle}" ${busy ? "disabled" : ""}>Remove</button>`
                : `<select id="dec-${esc(key)}">${opts}</select>
                   <button data-act="add" data-address="${esc(rec.address)}"
                     data-uuid="${esc(ch.uuid)}" data-handle="${ch.handle}"
                     data-name="${esc(ch.name)}" ${busy ? "disabled" : ""}>Add as sensor</button>`;
            }
            return `<div class="char">
              <div><b>${esc(ch.name)}</b> ${props}</div>
              <div class="mac">${esc(ch.uuid)}</div>
              ${valueHtml}
              <div>${addHtml}</div>
            </div>`;
          })
          .join("");
        return `<div class="svc">${esc(svc.name)} <span class="mac">${esc(svc.uuid)}</span></div>${chars}`;
      })
      .join("");
  }

  /* ---------- interactions ---------- */

  _onDrawerClick(ev) {
    const el = ev.target.closest("[data-act], select");
    if (!el) return;
    if (el.tagName === "SELECT") { ev.stopPropagation(); return; }
    const { act, address, uuid, handle, name } = el.dataset;
    if (act === "close") this._closeDrawer();
    else if (act === "probe") this._probe(address);
    else if (act === "add") this._add(address, uuid, handle, name);
    else if (act === "remove") this._remove(address, uuid, handle);
  }

  async _probe(address) {
    this._probes.set(address, { status: "running" });
    this._renderDrawer();
    try {
      const result = await this._hass.connection.sendMessagePromise({
        type: "ble_wizard/probe",
        address,
      });
      this._probes.set(address, { status: "done", result });
    } catch (err) {
      this._probes.set(address, {
        status: "error",
        error: err?.message || err?.code || "unknown error",
      });
    }
    if (this._drawer === address) this._renderDrawer();
  }

  async _add(address, uuid, handle, name) {
    const key = `${address}|${uuid}|${handle}`;
    const select = this._root.getElementById(`dec-${key}`);
    const decoder = select ? select.value : "hex";
    this._busy.add(key);
    this._renderDrawer();
    try {
      await this._hass.connection.sendMessagePromise({
        type: "ble_wizard/add_characteristic",
        address,
        char_uuid: uuid,
        char_handle: Number(handle),
        decoder,
        name,
      });
      this._markAdded(address, uuid, Number(handle), true);
    } catch (err) {
      alert(`Adding sensor failed: ${err?.message || err?.code || "unknown error"}`);
    }
    this._busy.delete(key);
    this._renderDrawer();
  }

  async _remove(address, uuid, handle) {
    const key = `${address}|${uuid}|${handle}`;
    this._busy.add(key);
    this._renderDrawer();
    try {
      await this._hass.connection.sendMessagePromise({
        type: "ble_wizard/remove_characteristic",
        address,
        char_uuid: uuid,
        char_handle: Number(handle),
      });
      this._markAdded(address, uuid, Number(handle), false);
    } catch (err) {
      alert(`Removing sensor failed: ${err?.message || err?.code || "unknown error"}`);
    }
    this._busy.delete(key);
    this._renderDrawer();
  }

  _markAdded(address, uuid, handle, added) {
    const probe = this._probes.get(address);
    if (probe?.result) {
      for (const svc of probe.result.services) {
        for (const ch of svc.characteristics) {
          if (ch.uuid === uuid && ch.handle === handle) ch.added = added;
        }
      }
    }
  }
}

customElements.define("ble-wizard-panel", BleWizardPanel);
