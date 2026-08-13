import { InterfaceRefresh } from "../api/client";
import { StatusIndicator } from "./StatusIndicator";

export function InterfaceDetailsDrawer({ port, onClose }: { port: InterfaceRefresh | null; onClose: () => void }) {
  if (!port) return null;
  return <aside className="details-drawer"><div className="drawer-heading"><div><span className="section-kicker">INTERFACE</span><h2>{port.name}</h2></div><button className="icon-button" type="button" onClick={onClose} aria-label="Close interface details">×</button></div><StatusIndicator state={port.operational_state} /><dl><dt>Description</dt><dd>{port.description || "No description"}</dd><dt>Administrative</dt><dd>{port.admin_state}</dd><dt>Operational</dt><dd>{port.operational_state}</dd><dt>VLAN / mode</dt><dd>{port.vlan || "-"} / {port.mode || "-"}</dd><dt>Speed / duplex</dt><dd>{port.speed || "-"} / {port.duplex || "-"}</dd><dt>Neighbor</dt><dd>{port.neighbor || "None discovered"}</dd></dl></aside>;
}
