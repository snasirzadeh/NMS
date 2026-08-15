import { ConnectionTest, Device } from "../api/client";
import { ConnectionTestResult } from "./ConnectionTestResult";

export function DeviceHeader({ device, refreshing, onRefresh, onTest, testResult }: { device: Device; refreshing: boolean; onRefresh: () => void; onTest: () => void; testResult: ConnectionTest | null }) {
  const label = device.last_connection_status === "success" ? "Active" : device.last_connection_status === "failed" ? "SSH Failed" : "Not Tested";
  return <header className="device-header"><div><span className="eyebrow">DEVICE DETAIL / {device.device_type.toUpperCase()}</span><h1>{device.display_name}</h1><p className="lede">{device.hostname} · {device.management_ip}</p><span className={`connection-state state-${device.last_connection_status}`}><i />{label}</span></div><div className="header-actions"><button className="button-secondary" type="button" onClick={onTest}>Test SSH</button><button type="button" onClick={onRefresh} disabled={refreshing}>{refreshing ? "Refreshing..." : "Refresh device"}</button><ConnectionTestResult result={testResult} /></div></header>;
}
