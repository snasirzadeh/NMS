import { useState } from "react";
import { devicesApi } from "../api/client";

const commands = ["show version", "show inventory", "show interfaces status", "show ip interface brief", "show vlan brief", "show cdp neighbors detail", "show lldp neighbors detail", "show running-config"];
export function TerminalPanel({ deviceId }: { deviceId: number }) {
  const [command, setCommand] = useState(commands[0]); const [output, setOutput] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  const execute = async () => { setBusy(true); setError(""); try { setOutput((await devicesApi.show(deviceId, command)).output); } catch (reason) { setError((reason as Error).message); } finally { setBusy(false); } };
  return <section className="terminal-panel"><div className="form-actions"><select value={command} onChange={(event) => setCommand(event.target.value)}>{commands.map((item) => <option key={item}>{item}</option>)}</select><button type="button" onClick={execute} disabled={busy}>{busy ? "Running..." : "Run command"}</button></div>{error ? <p className="form-error">{error}</p> : null}<pre>{output || "No command output"}</pre></section>;
}
