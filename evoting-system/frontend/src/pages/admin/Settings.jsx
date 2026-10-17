import { useAuth } from "../../contexts/AuthContext";
import AdminLayout from "../../layouts/AdminLayout";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import ThemeToggle from "../../components/ui/ThemeToggle";

export default function Settings() {
  const { user } = useAuth();

  return (
    <AdminLayout>
      <h1 className="mb-6 font-display text-2xl text-ink_text">Settings</h1>

      <Card className="mb-6 p-6">
        <h2 className="mb-4 text-sm font-semibold text-ink_text">Account</h2>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between border-b border-line pb-3">
            <dt className="text-muted">Name</dt>
            <dd className="text-ink_text">{user?.name}</dd>
          </div>
          <div className="flex justify-between border-b border-line pb-3">
            <dt className="text-muted">Email</dt>
            <dd className="text-ink_text">{user?.email}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-muted">Role</dt>
            <dd>
              <Badge tone="brass">{user?.role === "super_admin" ? "Super Admin" : "Election Admin"}</Badge>
            </dd>
          </div>
        </dl>
      </Card>

      <Card className="p-6">
        <h2 className="mb-4 text-sm font-semibold text-ink_text">Appearance</h2>
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted">Light / dark theme</p>
          <ThemeToggle />
        </div>
      </Card>

      {user?.role === "super_admin" && (
        <p className="mt-6 text-xs text-muted">
          Creating additional Super Admins or Election Admins is currently done via the
          <code className="mx-1 rounded bg-ink/5 px-1.5 py-0.5 font-hash dark:bg-white/5">
            flask create-super-admin
          </code>
          CLI command — an in-app admin management screen can be added here if needed.
        </p>
      )}
    </AdminLayout>
  );
}
