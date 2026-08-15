import { ConnectionTest } from "../api/client";

export function ConnectionTestResult({ result }: { result: ConnectionTest | null }) {
  if (!result) return null;
  return <div className={`connection-result ${result.success ? "result-success" : "result-failure"}`}><strong>{result.success ? "Connection successful" : "Connection failed"}</strong><span>{result.message} · SSH workflow {result.duration_ms} ms</span>{result.success ? <span>{result.hostname}{result.model ? ` · ${result.model}` : ""}{result.software_version ? ` · IOS ${result.software_version}` : ""}{result.uptime_text ? ` · ${result.uptime_text}` : ""}</span> : null}</div>;
}
