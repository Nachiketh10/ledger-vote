import { Link } from "react-router-dom";
import { ScanFace, CheckCircle2, XCircle } from "lucide-react";
import VoterLayout from "../../layouts/VoterLayout";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import { useAuth } from "../../contexts/AuthContext";

export default function Profile() {
  const { user } = useAuth();

  return (
    <VoterLayout>
      <div className="mx-auto max-w-lg">
        <h1 className="mb-8 font-display text-2xl text-ink_text">Your Profile</h1>

        <Card className="mb-6 p-6">
          <dl className="space-y-3 text-sm">
            <Row label="Name" value={user?.name} />
            <Row label="Email" value={user?.email} />
            <Row label="Voter ID" value={<span className="font-hash">{user?.voter_id}</span>} />
            <Row
              label="Verification status"
              value={
                user?.is_verified ? (
                  <Badge tone="verified">Verified</Badge>
                ) : (
                  <Badge tone="brass">Pending admin verification</Badge>
                )
              }
            />
          </dl>
        </Card>

        <Card className="p-6">
          <h2 className="mb-4 text-sm font-semibold text-ink_text">Biometric registration</h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm text-ink_text">
                <ScanFace size={16} /> Face
              </span>
              {user?.has_face_registered ? (
                <Badge tone="verified">
                  <CheckCircle2 size={12} /> Registered
                </Badge>
              ) : (
                <Button as={Link} to="/voter/register-face" size="sm" variant="outline">
                  Register
                </Button>
              )}
            </div>
            {!user?.has_face_registered && (
              <p className="flex items-center gap-1.5 pt-2 text-xs text-alert">
                <XCircle size={13} /> Face registration is required before you can vote.
              </p>
            )}
          </div>
        </Card>
      </div>
    </VoterLayout>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between border-b border-line pb-3 last:border-0 last:pb-0">
      <dt className="text-muted">{label}</dt>
      <dd className="text-ink_text">{value}</dd>
    </div>
  );
}
