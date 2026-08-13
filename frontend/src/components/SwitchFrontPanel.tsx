import { InterfaceRefresh } from "../api/client";
import { SwitchPort } from "./SwitchPort";

export function SwitchFrontPanel({ interfaces, refreshed, onSelect }: { interfaces: InterfaceRefresh[]; refreshed: boolean; onSelect: (item: InterfaceRefresh) => void }) {
  const ports = interfaces.length ? interfaces : Array.from({ length: 24 }, (_, index) => ({ name: `Port-${String(index + 1).padStart(2, "0")}`, description: "", admin_state: "unknown", operational_state: "unknown", vlan: "", mode: "", speed: "", duplex: "", neighbor: null }));
  return <section className="switch-panel"><div className="switch-panel-top"><div><span className="section-kicker">HARDWARE VIEW</span><h2>Switch front panel</h2></div><span className="panel-state">{refreshed ? `${interfaces.length} interfaces` : "Awaiting refresh"}</span></div><div className="switch-face"><div className="switch-brand">NMS <small>managed switch</small></div><div className="port-bank">{ports.map((port) => <SwitchPort key={port.name} port={port} onSelect={() => onSelect(port)} />)}</div></div></section>;
}
