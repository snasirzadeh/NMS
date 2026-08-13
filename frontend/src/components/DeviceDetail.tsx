import { FormEvent, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { ConfigPreview, ConnectionTest, Device, DeviceRefresh, devicesApi, InterfaceRefresh } from "../api/client";
import { BackupPanel } from "./BackupPanel";
import { DeviceHeader } from "./DeviceHeader";
import { InterfaceDetailsDrawer } from "./InterfaceDetailsDrawer";
import { SwitchFrontPanel } from "./SwitchFrontPanel";
import { TerminalPanel } from "./TerminalPanel";

const tabs = ["Overview", "Interfaces", "VLANs", "Neighbors", "Configuration", "CLI", "Backups"];

export function DeviceDetail() {
  const { deviceId } = useParams();
  const id = Number(deviceId);
  const [device, setDevice] = useState<Device | null>(null);
  const [data, setData] = useState<DeviceRefresh | null>(null);
  const [selected, setSelected] = useState<InterfaceRefresh | null>(null);
  const [tab, setTab] = useState("Overview");
  const [error, setError] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [testResult, setTestResult] = useState<ConnectionTest | null>(null);

  useEffect(() => { devicesApi.get(id).then(setDevice).catch((reason: Error) => setError(reason.message)); }, [id]);
  const refresh = async () => { setRefreshing(true); setError(""); try { setData(await devicesApi.refresh(id)); } catch (reason) { setError((reason as Error).message); } finally { setRefreshing(false); } };
  const test = async () => { try { setTestResult(await devicesApi.testConnection(id)); } catch (reason) { setError((reason as Error).message); } };
  if (!device) return <section className="empty-state">{error ? <p className="form-error">{error}</p> : <p>Loading device...</p>}</section>;

  return <>
    <DeviceHeader device={device} refreshing={refreshing} onRefresh={refresh} onTest={test} testResult={testResult} />
    {error ? <p className="form-error page-error">{error}</p> : null}
    <div className="detail-tabs">{tabs.map((item) => <button key={item} className={tab === item ? "active" : ""} type="button" onClick={() => setTab(item)}>{item}</button>)}</div>
    {tab === "Overview" ? <><SwitchFrontPanel interfaces={data?.interfaces ?? []} refreshed={Boolean(data)} onSelect={setSelected} /><Facts device={device} data={data} /></> : null}
    {tab === "Interfaces" ? <InterfaceTable interfaces={data?.interfaces ?? []} onSelect={setSelected} /> : null}
    {tab === "VLANs" ? <SimpleTable headers={["VLAN", "Name", "Status"]} rows={(data?.vlans ?? []).map((item) => [String(item.vlan_id), item.name, item.status])} empty="No VLAN data fetched." /> : null}
    {tab === "Neighbors" ? <SimpleTable headers={["Local interface", "Device", "Remote interface", "Protocol", "Platform"]} rows={(data?.neighbors ?? []).map((item) => [item.local_interface, item.device_id, item.remote_interface, item.protocol, item.platform])} empty="No neighbors fetched." /> : null}
    {tab === "Configuration" ? <ConfigurationPanel deviceId={id} /> : null}
    {tab === "CLI" ? <TerminalPanel deviceId={id} /> : null}
    {tab === "Backups" ? <BackupPanel deviceId={id} /> : null}
    <InterfaceDetailsDrawer port={selected} onClose={() => setSelected(null)} />
  </>;
}

function Facts({ device, data }: { device: Device; data: DeviceRefresh | null }) { const facts = [["Hostname", data?.facts.hostname || device.hostname], ["Model", data?.facts.model || device.model || "Not fetched"], ["Serial", data?.facts.serial || device.serial_number || "Not fetched"], ["Software", data?.facts.software_version || device.software_version || "Not fetched"], ["Uptime", data?.facts.uptime || device.uptime_text || "Not fetched"]]; return <section className="facts-grid">{facts.map(([label, value]) => <div key={label}><span>{label}</span><strong>{value}</strong></div>)}</section>; }
function InterfaceTable({ interfaces, onSelect }: { interfaces: InterfaceRefresh[]; onSelect: (item: InterfaceRefresh) => void }) { return <section className="device-panel table-panel"><div className="panel-heading"><h2>Interfaces</h2><span className="record-count">{interfaces.length} fetched</span></div><div className="detail-table"><div className="detail-row detail-head"><span>Name</span><span>Description</span><span>State</span><span>VLAN</span><span>Speed</span></div>{interfaces.map((item) => <button className="detail-row" key={item.name} type="button" onClick={() => onSelect(item)}><strong>{item.name}</strong><span>{item.description || "-"}</span><span>{item.operational_state}</span><span>{item.vlan || item.mode || "-"}</span><span>{item.speed || "-"}</span></button>)}{!interfaces.length ? <p className="empty-copy">Refresh the device to retrieve interfaces.</p> : null}</div></section>; }
function SimpleTable({ headers, rows, empty }: { headers: string[]; rows: string[][]; empty: string }) { return <section className="device-panel table-panel"><div className="detail-table"><div className="detail-row detail-head">{headers.map((item) => <span key={item}>{item}</span>)}</div>{rows.map((row, index) => <div className="detail-row" key={`${row[0]}-${index}`}>{row.map((item, cell) => <span key={`${cell}-${item}`}>{item || "-"}</span>)}</div>)}{!rows.length ? <p className="empty-copy">{empty}</p> : null}</div></section>; }
function ConfigurationPanel({ deviceId }: { deviceId: number }) { const [text, setText] = useState(""); const [preview, setPreview] = useState<ConfigPreview | null>(null); const [audit, setAudit] = useState(""); const [error, setError] = useState(""); const runPreview = async (event: FormEvent) => { event.preventDefault(); setError(""); setAudit(""); try { setPreview(await devicesApi.previewConfig(deviceId, text.split("\n"))); } catch (reason) { setError((reason as Error).message); } }; const apply = async () => { if (!preview) return; try { setAudit((await devicesApi.applyConfig(deviceId, preview.confirmation_token)).message); } catch (reason) { setError((reason as Error).message); } }; return <form className="device-panel config-panel" onSubmit={runPreview}><div><span className="section-kicker">SAFE CONFIGURATION</span><h2>Command preview</h2></div><textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="interface Gi1/0/1\ndescription uplink" spellCheck="false" />{error ? <p className="form-error">{error}</p> : null}<div className="form-actions"><button type="submit">Preview commands</button>{preview ? <button type="button" className="button-secondary" onClick={apply}>Confirm apply</button> : null}</div>{preview ? <div className="config-preview"><strong>Preview ready</strong>{preview.commands.map((command) => <code key={command}>{command}</code>)}{audit ? <span>{audit}</span> : null}</div> : null}</form>; }
