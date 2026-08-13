import { useEffect, useRef } from "react";
import cytoscape, { Core, ElementDefinition } from "cytoscape";
import { Topology } from "../api/client";

export function TopologyCanvas({ topology, onManagedNode, onUnmanagedNode }: { topology: Topology; onManagedNode: (deviceId: number) => void; onUnmanagedNode: (hostname: string) => void }) {
  const host = useRef<HTMLDivElement>(null); const graph = useRef<Core | null>(null);
  useEffect(() => {
    if (!host.current) return;
    const elements: ElementDefinition[] = [
      ...topology.nodes.map((node) => ({ data: { id: node.id, label: node.label, hostname: node.hostname, managed: node.managed, deviceId: node.device_id } })),
      ...topology.edges.map((edge) => ({ data: { id: edge.id, source: edge.source, target: edge.target, label: `${edge.source_interface}  ·  ${edge.destination_interface}`, protocol: edge.protocol } })),
    ];
    graph.current?.destroy();
    const instance = cytoscape({ container: host.current, elements, layout: { name: "cose", animate: false, padding: 34 }, style: [
      { selector: "node", style: { "background-color": "#2d7cc2", "border-color": "#77b9ef", "border-width": 2, color: "#e8edf4", label: "data(label)", "font-size": 12, "text-valign": "center", "text-halign": "center", shape: "round-rectangle", width: 150, height: 52, "text-wrap": "ellipsis", "text-max-width": 130 } as any },
      { selector: "node[managed = false]", style: { "background-color": "#303842", "border-color": "#8b98a8", "border-style": "dashed", "color": "#c3ccd7", shape: "hexagon" } as any },
      { selector: "edge", style: { width: 1.5, "line-color": "#5b7185", "target-arrow-color": "#5b7185", "target-arrow-shape": "triangle", label: "data(label)", color: "#93a1b2", "font-size": 9, "text-background-color": "#171f29", "text-background-opacity": 1, "text-background-padding": 3, "curve-style": "bezier" } as any },
    ], userZoomingEnabled: true, userPanningEnabled: true });
    instance.on("tap", "node", (event) => { const node = event.target; if (node.data("managed")) onManagedNode(Number(node.data("deviceId"))); else onUnmanagedNode(String(node.data("hostname"))); });
    graph.current = instance;
    return () => { instance.destroy(); graph.current = null; };
  }, [topology, onManagedNode, onUnmanagedNode]);
  return <div className="topology-canvas"><div className="topology-tools"><button type="button" onClick={() => graph.current?.fit()}>Fit</button><button type="button" onClick={() => graph.current?.zoom({ level: (graph.current?.zoom() ?? 1) + .15, renderedPosition: { x: 450, y: 220 } })}>+</button><button type="button" onClick={() => graph.current?.zoom({ level: Math.max(.2, (graph.current?.zoom() ?? 1) - .15), renderedPosition: { x: 450, y: 220 } })}>−</button></div><div className="topology-legend"><span><i className="legend-managed" /> Managed</span><span><i className="legend-unmanaged" /> Discovered / Unmanaged</span></div><div className="cy-container" ref={host} /></div>;
}
