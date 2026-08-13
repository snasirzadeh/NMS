import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Group, groupsApi, Topology } from "../api/client";
import { TopologyCanvas } from "./TopologyCanvas";

export function TopologyPage() {
  const navigate = useNavigate(); const [groups, setGroups] = useState<Group[]>([]); const [groupId, setGroupId] = useState<number | null>(null); const [topology, setTopology] = useState<Topology | null>(null); const [error, setError] = useState(""); const [discovering, setDiscovering] = useState(false); const [notice, setNotice] = useState("");
  useEffect(() => { groupsApi.list().then((items) => { setGroups(items); if (items[0]) setGroupId(items[0].id); }).catch((reason: Error) => setError(reason.message)); }, []);
  useEffect(() => { if (groupId) groupsApi.topology(groupId).then(setTopology).catch((reason: Error) => setError(reason.message)); }, [groupId]);
  const discover = async () => { if (!groupId) return; setDiscovering(true); setError(""); setNotice(""); try { const result = await groupsApi.discoverTopology(groupId); setTopology(result); setNotice(`${result.refreshed_devices} device(s) discovered`); } catch (reason) { setError((reason as Error).message); } finally { setDiscovering(false); } };
  const openManaged = useCallback((id: number) => navigate(`/devices/${id}`), [navigate]);
  const openUnmanaged = useCallback((hostname: string) => navigate(`/devices?hostname=${encodeURIComponent(hostname)}`), [navigate]);
  return <><header className="page-header"><div><span className="eyebrow">DISCOVERY GRAPH</span><h1>Topology</h1><p className="lede">Review explicit CDP and LLDP discovery results by group.</p></div><div className="header-actions"><select value={groupId ?? ""} onChange={(event) => setGroupId(Number(event.target.value))}><option value="">Select group</option>{groups.map((group) => <option value={group.id} key={group.id}>{group.name}</option>)}</select><button type="button" onClick={discover} disabled={!groupId || discovering}>{discovering ? "Discovering..." : "Discover topology"}</button></div></header>{error ? <p className="form-error page-error">{error}</p> : null}{notice ? <p className="topology-notice">{notice}</p> : null}{topology ? <TopologyCanvas topology={topology} onManagedNode={openManaged} onUnmanagedNode={openUnmanaged} /> : <section className="empty-state"><p>Select a group to view its topology.</p></section>}</>;
}
