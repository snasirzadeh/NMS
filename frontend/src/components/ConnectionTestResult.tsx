import { ConnectionTest } from "../api/client";

export function ConnectionTestResult({ result }: { result: ConnectionTest | null }) {
  if (!result) return null;
  return <div className={`connection-result ${result.success ? "result-success" : "result-failure"}`}><strong>{result.success ? "Connection successful" : "Connection failed"}</strong><span>{result.message} · {result.duration_ms} ms</span></div>;
}
