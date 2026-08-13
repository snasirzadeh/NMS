import { InterfaceRefresh } from "../api/client";
import { StatusIndicator } from "./StatusIndicator";

export function SwitchPort({ port, onSelect }: { port: InterfaceRefresh; onSelect: () => void }) {
  return <button className="switch-port" type="button" onClick={onSelect} title={`${port.name} ${port.operational_state}`}><span className="port-light" /><b>{port.name.split("/").at(-1)}</b><StatusIndicator state={port.operational_state} /></button>;
}
