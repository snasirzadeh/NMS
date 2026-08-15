const apiBase = "/api/v1";
let csrfToken = "";

function setCsrf(value?: string | null) { csrfToken = value ?? ""; }

function csrfCookie(): string {
  if (typeof document === "undefined") return "";
  const prefix = "nms_csrf=";
  const value = document.cookie.split("; ").find((item) => item.startsWith(prefix));
  return value ? decodeURIComponent(value.slice(prefix.length)) : "";
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (options.method && !["GET", "HEAD", "OPTIONS"].includes(options.method)) {
    // The readable CSRF cookie is the durable source of truth across reloads and
    // remounts. Keep the response value as a fallback for non-browser tests.
    headers.set("X-CSRF-Token", csrfCookie() || csrfToken);
  }
  const response = await fetch(`${apiBase}${path}`, { ...options, headers, credentials: "same-origin" });
  if (!response.ok) {
    const body = await response.json().catch(() => null) as { detail?: string } | null;
    throw new Error(body?.detail ?? `Request failed with ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type AuthSession = { authenticated: boolean; configured: boolean; username: string | null; csrf_token: string | null; expires_at: string | null };
export type Group = { id: number; name: string; description: string | null; parent_id: number | null; children?: Group[]; device_count?: number };
export type Credential = { id: number; name: string; username: string; key_type: string; key_bits: number | null; key_fingerprint: string; public_key_fingerprint: string | null; created_at: string; updated_at: string; usage_count: number };
export type Device = {
  id: number; group_id: number; display_name: string; hostname: string; management_ip: string;
  device_type: string; platform: string | null; ssh_port: number; ssh_credential_id: number | null;
  ssh_profile: "modern" | "cisco_legacy"; description: string | null; site: string | null; rack: string | null;
  serial_number: string | null; model: string | null; software_version: string | null; uptime_text: string | null;
  trusted_host_key_fingerprint: string | null; trusted_host_key_algorithm: string | null;
  last_connection_status: "unknown" | "success" | "failed"; last_connection_test_at: string | null;
  last_connection_error_code: string | null;
};
export type ConnectionTest = { success: boolean; message: string; hostname: string; duration_ms: number; error_code: string | null; host_key: { fingerprint: string | null; algorithm: string | null } | null; model: string | null; software_version: string | null; uptime_text: string | null };
export type InterfaceRefresh = { name: string; description: string; admin_state: string; operational_state: string; vlan: string; mode: string; speed: string; duplex: string; neighbor: string | null };
export type DeviceRefresh = { facts: { hostname: string; model: string; serial: string; software_version: string; uptime: string }; interfaces: InterfaceRefresh[]; vlans: { vlan_id: number; name: string; status: string }[]; neighbors: { local_interface: string; device_id: string; remote_interface: string; protocol: string; platform: string }[] };
export type ConfigPreview = { commands: string[]; confirmation_token: string; expires_at: number };
export type ConfigAudit = { accepted: boolean; executed: boolean; message: string };
export type TopologyNode = { id: string; label: string; hostname: string; managed: boolean; device_id: number | null };
export type TopologyEdge = { id: string; source: string; target: string; source_interface: string; destination_interface: string; protocol: string; discovered_at: string };
export type Topology = { group_id: number; nodes: TopologyNode[]; edges: TopologyEdge[]; refreshed_devices?: number; skipped_devices?: string[] };
export type BackupSummary = { id: number; device_id: number; checksum: string; created_at: string };
export type Backup = BackupSummary & { configuration: string };

function acceptSession(session: AuthSession) { setCsrf(session.csrf_token); return session; }

export const authApi = {
  session: async () => acceptSession(await request<AuthSession>("/auth/session")),
  setup: async (username: string, password: string, password_confirmation: string) => acceptSession(await request<AuthSession>("/auth/setup", { method: "POST", body: JSON.stringify({ username, password, password_confirmation }) })),
  login: async (username: string, password: string) => acceptSession(await request<AuthSession>("/auth/login", { method: "POST", body: JSON.stringify({ username, password }) })),
  logout: async () => { await request<void>("/auth/logout", { method: "POST" }); setCsrf(""); },
  changePassword: async (current_password: string, new_password: string, new_password_confirmation: string) => acceptSession(await request<AuthSession>("/auth/password", { method: "POST", body: JSON.stringify({ current_password, new_password, new_password_confirmation }) })),
};

export const credentialsApi = {
  list: () => request<Credential[]>("/credentials"),
  save: (name: string, username: string, privateKey: string, passphrase: string, file?: File) => {
    const body = new FormData(); body.append("name", name); body.append("username", username); body.append("private_key", privateKey); if (passphrase) body.append("passphrase", passphrase); if (file) body.append("key_file", file);
    return request<Credential>("/credentials", { method: "POST", body });
  },
  replace: (id: number, privateKey: string, passphrase: string, file?: File) => {
    const body = new FormData(); body.append("private_key", privateKey); if (passphrase) body.append("passphrase", passphrase); if (file) body.append("key_file", file);
    return request<Credential>(`/credentials/${id}/replace`, { method: "POST", body });
  },
  remove: (id: number) => request<void>(`/credentials/${id}`, { method: "DELETE" }),
};

export const groupsApi = {
  tree: () => request<Group[]>("/groups/tree"), list: () => request<Group[]>("/groups"),
  create: (payload: { name: string; parent_id: number | null; description?: string }) => request<Group>("/groups", { method: "POST", body: JSON.stringify(payload) }),
  topology: (id: number) => request<Topology>(`/groups/${id}/topology`),
  discoverTopology: (id: number) => request<Topology>(`/groups/${id}/topology/discover`, { method: "POST" }),
};

export const devicesApi = {
  list: () => request<Device[]>("/devices"), get: (id: number) => request<Device>(`/devices/${id}`),
  create: (payload: Omit<Device, "id" | "uptime_text" | "trusted_host_key_fingerprint" | "trusted_host_key_algorithm" | "last_connection_status" | "last_connection_test_at" | "last_connection_error_code">) => request<Device>("/devices", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: number, payload: Partial<Device>) => request<Device>(`/devices/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
  testConnection: (id: number) => request<ConnectionTest>(`/devices/${id}/test-connection`, { method: "POST" }),
  trustHostKey: (id: number, fingerprint: string) => request<Device>(`/devices/${id}/host-key/trust`, { method: "POST", body: JSON.stringify({ fingerprint }) }),
  refresh: (id: number) => request<DeviceRefresh>(`/devices/${id}/refresh`, { method: "POST" }),
  show: (id: number, command: string) => request<{ command: string; output: string }>(`/devices/${id}/show`, { method: "POST", body: JSON.stringify({ command }) }),
  previewConfig: (id: number, commands: string[]) => request<ConfigPreview>(`/devices/${id}/config/preview`, { method: "POST", body: JSON.stringify({ commands }) }),
  applyConfig: (id: number, confirmation_token: string) => request<ConfigAudit>(`/devices/${id}/config/apply`, { method: "POST", body: JSON.stringify({ confirmation_token, confirmed: true }) }),
  backups: (id: number) => request<BackupSummary[]>(`/devices/${id}/backups`),
  createBackup: (id: number) => request<BackupSummary>(`/devices/${id}/backups`, { method: "POST" }),
};

export const backupsApi = { get: (id: number) => request<Backup>(`/backups/${id}`) };
