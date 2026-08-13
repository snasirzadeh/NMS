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

export const groupsApi = {
  tree: () => request<Group[]>("/groups/tree"),
  list: () => request<Group[]>("/groups"),
  create: (payload: { name: string; parent_id: number | null; description?: string }) =>
    request<Group>("/groups", { method: "POST", body: JSON.stringify(payload) }),
};

export const devicesApi = {
  list: () => request<Device[]>("/devices"),
  create: (payload: Omit<Device, "id" | "uptime_text">) =>
    request<Device>("/devices", { method: "POST", body: JSON.stringify(payload) }),
  previewSsh: (config: string) =>
    request<SSHPreview>("/devices/ssh-config/preview", { method: "POST", body: JSON.stringify({ config }) }),
};
