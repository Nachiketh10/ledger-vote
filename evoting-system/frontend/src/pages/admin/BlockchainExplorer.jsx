import { useEffect, useState } from "react";
import { ShieldCheck, ShieldX, Search, Link2 } from "lucide-react";
import AdminLayout from "../../layouts/AdminLayout";
import Card from "../../components/ui/Card";
import Badge from "../../components/ui/Badge";
import Button from "../../components/ui/Button";
import Skeleton from "../../components/ui/Skeleton";
import { inputClass } from "../../components/ui/FormField";
import { listBlocks, verifyChain, searchBlocks } from "../../services/blockchainService";
import { useToast } from "../../contexts/ToastContext";

export default function BlockchainExplorer() {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [blocks, setBlocks] = useState([]);
  const [verification, setVerification] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [searchValue, setSearchValue] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await listBlocks(1);
      setBlocks(data.items);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleVerify = async () => {
    setVerifying(true);
    try {
      const result = await verifyChain();
      setVerification(result);
      toast(result.chain_valid ? "Chain is fully valid." : "Tampering detected!", result.chain_valid ? "success" : "error");
    } finally {
      setVerifying(false);
    }
  };

  const handleSearch = async () => {
    if (!searchValue.trim()) return;
    setLoading(true);
    try {
      let result;
      if (searchValue.length === 64) {
        result = await searchBlocks({ hash: searchValue });
        setBlocks(result ? [result] : []);
      } else {
        result = await searchBlocks({ transaction_id: searchValue });
        setBlocks(result ? [result] : []);
      }
      if (!result) toast("No matching block found.", "info");
    } catch {
      toast("Search failed — check the value format.", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AdminLayout>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-2xl text-ink_text">Blockchain Explorer</h1>
        <Button onClick={handleVerify} disabled={verifying} variant="outline">
          <ShieldCheck size={15} /> {verifying ? "Verifying..." : "Verify full chain"}
        </Button>
      </div>

      {verification && (
        <Card
          className={`mb-6 flex items-center gap-3 p-4 ${
            verification.chain_valid ? "border-verified/40 bg-verified/5" : "border-alert/40 bg-alert/5"
          }`}
        >
          {verification.chain_valid ? (
            <ShieldCheck size={20} className="text-verified" />
          ) : (
            <ShieldX size={20} className="text-alert" />
          )}
          <div>
            <p className="text-sm font-medium text-ink_text">
              {verification.chain_valid
                ? `All ${verification.blocks_checked} blocks verified — chain is intact.`
                : `${verification.invalid_blocks.length} block(s) failed verification!`}
            </p>
            {!verification.chain_valid && (
              <ul className="mt-1 text-xs text-alert">
                {verification.invalid_blocks.map((b) => (
                  <li key={b.block_index}>Block #{b.block_index}: {b.issues.join("; ")}</li>
                ))}
              </ul>
            )}
          </div>
        </Card>
      )}

      <div className="mb-5 flex items-center gap-2">
        <div className="relative flex-1 max-w-md">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            className={`${inputClass} pl-9 font-hash`}
            placeholder="Search by transaction ID or hash"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
        </div>
        <Button variant="outline" size="sm" onClick={handleSearch}>Search</Button>
        <Button variant="ghost" size="sm" onClick={() => { setSearchValue(""); load(); }}>Reset</Button>
      </div>

      {loading ? (
        <Skeleton className="h-64 w-full" />
      ) : blocks.length === 0 ? (
        <p className="text-sm text-muted">No blocks found.</p>
      ) : (
        <div className="space-y-2">
          {blocks.map((b) => (
            <Card key={b.id} className="p-4">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 font-medium text-ink_text">
                  <Link2 size={15} className="text-seal" /> Block #{b.block_index}
                </span>
                <Badge tone="neutral">{new Date(b.timestamp).toLocaleString()}</Badge>
              </div>
              <div className="mt-2 space-y-1 font-hash text-xs text-muted">
                <p className="break-all">Hash: {b.current_hash}</p>
                <p className="break-all">Prev: {b.previous_hash}</p>
                <p className="break-all">Tx: {b.transaction_id}</p>
              </div>
            </Card>
          ))}
        </div>
      )}
    </AdminLayout>
  );
}
