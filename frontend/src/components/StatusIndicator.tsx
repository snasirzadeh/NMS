export function StatusIndicator({ state }: { state: string }) {
  const tone = state === "up" || state === "connected" ? "status-up" : state === "down" || state === "disabled" ? "status-down" : "status-neutral";
  return <span className={`status-indicator ${tone}`}><i />{state}</span>;
}
