import { NavLink, Route, Routes } from "react-router-dom";

const navigation = [
  { label: "Dashboard", path: "/" },
  { label: "Companies", path: "/companies" },
  { label: "Devices", path: "/devices" },
  { label: "Topology", path: "/topology" },
  { label: "Backups", path: "/backups" },
];

function Dashboard() {
  return (
    <>
      <header className="page-header">
        <div>
          <span className="eyebrow">OPERATIONS CONSOLE</span>
          <h1>Network workspace</h1>
          <p className="lede">A local control surface for deliberate Cisco switch management.</p>
        </div>
        <span className="environment-badge">LOCAL / READY</span>
      </header>
      <section className="device-panel" aria-labelledby="foundation-title">
        <div className="panel-copy">
          <span className="section-kicker">FOUNDATION</span>
          <h2 id="foundation-title">Inventory foundation is online</h2>
          <p>
            The API, database connection layer, migration system, and reverse proxy are ready for inventory workflows.
          </p>
        </div>
        <div className="signal-grid" aria-label="Foundation service status">
          <div><strong>API</strong><span>Available</span></div>
          <div><strong>DATABASE</strong><span>Compose service</span></div>
          <div><strong>SSH</strong><span>Explicit actions only</span></div>
        </div>
      </section>
      <section className="device-panel panel-secondary" aria-labelledby="preview-title">
        <div className="panel-copy">
          <span className="section-kicker">HARDWARE PREVIEW</span>
          <h2 id="preview-title">Neutral port surface</h2>
          <p>Port state stays unknown until a later explicit refresh supplies real interface data.</p>
        </div>
        <div className="port-bank" aria-label="Unknown switch-port preview">
          {Array.from({ length: 12 }, (_, index) => (
            <div className="port" key={index}>
              <span>{String(index + 1).padStart(2, "0")}</span>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <section className="empty-state">
      <span className="section-kicker">MODULE</span>
      <h1>{title}</h1>
      <p>This foundation view is ready for its implementation phase.</p>
    </section>
  );
}

export default function App() {
  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark">N</div>
          <div><strong>NMS</strong><span>NETWORK CONTROL</span></div>
        </div>
        <nav aria-label="Primary navigation">
          {navigation.map((item) => (
            <NavLink key={item.path} to={item.path} end={item.path === "/"}>
              <span className="nav-dot" aria-hidden="true" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <footer className="sidebar-footer"><span className="status-dot" /> Local workspace</footer>
      </aside>
      <section className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/companies" element={<PlaceholderPage title="Companies" />} />
          <Route path="/devices" element={<PlaceholderPage title="Devices" />} />
          <Route path="/topology" element={<PlaceholderPage title="Topology" />} />
          <Route path="/backups" element={<PlaceholderPage title="Backups" />} />
        </Routes>
      </section>
    </main>
  );
}
