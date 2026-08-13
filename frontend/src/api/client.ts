const apiBase = "/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    headers: { "Content-Type": "application/json", ...(options?.headers ?? {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed with ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type Group = {
  id: number;
  name: string;
  description: string | null;
  parent_id: number | null;
  children?: Group[];
  device_count?: number;
};

export type Device = {
  id: number;
  group_id: number;
  display_name: string;
  hostname: string;
  management_ip: string;
  device_type: string;
  platform: string | null;
  ssh_port: number;
  ssh_config: string | null;
  description: string | null;
  site: string | null;
  rack: string | null;
  serial_number: string | null;
  model: string | null;
  software_version: string | null;
  uptime_text: string | null;
};

export type SSHPreview = {
  host: string;
  hostname: string;
  user: string;
  port: number;
  identities_only: boolean;
  identity_file_relative: string;
  identity_file_exists: boolean;
  algorithms: Record<string, string>;
  warnings: string[];
};

export type ConnectionTest = {
  success: boolean;
  message: string;
  hostname: string;
  duration_ms: number;
};

export type InterfaceRefresh = { name: string; description: string; admin_state: string; operational_state: string; vlan: string; mode: string; speed: string; duplex: string; neighbor: string | null };
export type DeviceRefresh = { facts: { hostname: string; model: string; serial: string; software_version: string; uptime: string }; interfaces: InterfaceRefresh[]; vlans: { vlan_id: number; name: string; status: string }[]; neighbors: { local_interface: string; device_id: string; remote_interface: string; protocol: string; platform: string }[] };
export type ConfigPreview = { commands: string[]; confirmation_token: string; expires_at: number };
export type ConfigAudit = { accepted: boolean; executed: boolean; message: string };

export const groupsApi = {
  tree: () => request<Group[]>("/groups/tree"),
  list: () => request<Group[]>("/groups"),
  create: (payload: { name: string; parent_id: number | null; description?: string }) =>
    request<Group>("/groups", { method: "POST", body: JSON.stringify(payload) }),
};

export const devicesApi = {
  list: () => request<Device[]>("/devices"),
  get: (deviceId: number) => request<Device>(`/devices/${deviceId}`),
  create: (payload: Omit<Device, "id" | "uptime_text">) =>
    request<Device>("/devices", { method: "POST", body: JSON.stringify(payload) }),
  previewSsh: (config: string) =>
    request<SSHPreview>("/devices/ssh-config/preview", { method: "POST", body: JSON.stringify({ config }) }),
  testConnection: (deviceId: number) =>
    request<ConnectionTest>(`/devices/${deviceId}/test-connection`, { method: "POST" }),
  refresh: (deviceId: number) => request<DeviceRefresh>(`/devices/${deviceId}/refresh`, { method: "POST" }),
  show: (deviceId: number, command: string) => request<{ command: string; output: string }>(`/devices/${deviceId}/show`, { method: "POST", body: JSON.stringify({ command }) }),
  previewConfig: (deviceId: number, commands: string[]) => request<ConfigPreview>(`/devices/${deviceId}/config/preview`, { method: "POST", body: JSON.stringify({ commands }) }),
  applyConfig: (deviceId: number, confirmation_token: string) => request<ConfigAudit>(`/devices/${deviceId}/config/apply`, { method: "POST", body: JSON.stringify({ confirmation_token, confirmed: true }) }),
};
