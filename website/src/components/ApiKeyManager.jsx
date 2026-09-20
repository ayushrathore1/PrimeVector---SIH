import React, { useState, useEffect, useCallback } from 'react';
import { Key, Plus, Copy, Check, ShieldAlert, Trash2, CheckCircle2, AlertTriangle, RefreshCw, Layers } from 'lucide-react';
import { createApiKey, listApiKeys, revokeApiKey } from '../utils/api';

export default function ApiKeyManager({ activeApiKey, onSelectKey }) {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Form state for creating a new key
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [keyName, setKeyName] = useState('');
  const [keyTier, setKeyTier] = useState('free');
  const [creating, setCreating] = useState(false);

  // Newly generated key modal state
  const [newlyCreatedKey, setNewlyCreatedKey] = useState(null);
  const [copiedNewKey, setCopiedNewKey] = useState(false);

  // Revoking state
  const [revokingId, setRevokingId] = useState(null);

  const fetchKeys = useCallback(async () => {
    if (!activeApiKey) return;
    setLoading(true);
    setError(null);
    const res = await listApiKeys(activeApiKey);
    if (res.success && res.data?.keys) {
      setKeys(res.data.keys);
    } else {
      setKeys([]);
      if (res.error) setError('Could not fetch keys from Gateway. Verify active API key.');
    }
    setLoading(false);
  }, [activeApiKey]);

  useEffect(() => {
    fetchKeys();
  }, [fetchKeys]);

  const handleCreateKey = async (e) => {
    e.preventDefault();
    if (!keyName.trim()) return;

    setCreating(true);
    setError(null);
    const res = await createApiKey(activeApiKey, keyName.trim(), keyTier);
    setCreating(false);

    if (res.success && res.data) {
      setNewlyCreatedKey(res.data);
      setKeyName('');
      setKeyTier('free');
      setShowCreateModal(false);
      // Auto-select the newly created key if requested or update list
      fetchKeys();
    } else {
      setError(res.error || 'Failed to create API key');
    }
  };

  const handleRevokeKey = async (keyId) => {
    if (!window.confirm('Are you sure you want to revoke this API key? This action cannot be undone.')) return;

    setRevokingId(keyId);
    const res = await revokeApiKey(activeApiKey, keyId);
    setRevokingId(null);

    if (res.success) {
      fetchKeys();
    } else {
      alert('Failed to revoke API key');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedNewKey(true);
    setTimeout(() => setCopiedNewKey(false), 2500);
  };

  return (
    <div className="bg-white border border-forest/10 rounded-2xl p-6 sm:p-8 space-y-6 shadow-spade spade-cut-md">
      
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-forest/10">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-mono font-semibold uppercase tracking-wider text-forest/70 mb-1">
            <Key size={14} className="text-forest" />
            <span>Key Management & Authentication</span>
          </div>
          <h2 className="font-display text-2xl font-extrabold text-forest tracking-tight">
            API Keys & Provisioning
          </h2>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchKeys}
            disabled={loading}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-sage-1 border border-forest/15 hover:border-forest/40 text-forest font-mono text-xs font-semibold transition-colors disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>

          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-forest text-lemongrass hover:bg-forest-hover font-mono text-xs font-bold transition-all shadow-sm cursor-pointer"
          >
            <Plus size={15} />
            <span>Generate New API Key</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs font-mono">
          <AlertTriangle size={15} className="shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Newly Created Key Secret Banner / Modal */}
      {newlyCreatedKey && (
        <div className="p-5 rounded-xl bg-emerald-950 text-white border border-emerald-500/40 space-y-4 shadow-xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-emerald-400 font-mono text-xs font-bold uppercase tracking-wider">
              <CheckCircle2 size={16} />
              <span>API Key Successfully Created</span>
            </div>
            <button
              onClick={() => setNewlyCreatedKey(null)}
              className="text-white/60 hover:text-white text-xs font-mono cursor-pointer"
            >
              Close Notice ✕
            </button>
          </div>

          <p className="text-xs text-emerald-200/90 leading-relaxed font-normal">
            Please copy your secret key now. <strong className="text-white">It will not be displayed again</strong> for safety reasons.
          </p>

          <div className="flex flex-col sm:flex-row items-center gap-3 bg-black/50 p-3 rounded-lg border border-emerald-500/30">
            <code className="text-sm font-mono font-bold text-lemongrass select-all break-all w-full sm:w-auto">
              {newlyCreatedKey.api_key}
            </code>
            <div className="flex items-center gap-2 shrink-0 ml-auto">
              <button
                onClick={() => copyToClipboard(newlyCreatedKey.api_key)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-lemongrass text-forest hover:bg-lemongrass-hover font-mono text-xs font-bold transition-colors cursor-pointer"
              >
                {copiedNewKey ? <Check size={14} /> : <Copy size={14} />}
                <span>{copiedNewKey ? 'Copied!' : 'Copy Key'}</span>
              </button>
              <button
                onClick={() => {
                  onSelectKey(newlyCreatedKey.api_key);
                  setNewlyCreatedKey(null);
                }}
                className="px-3 py-1.5 rounded bg-white/20 hover:bg-white/30 text-white font-mono text-xs font-bold transition-colors cursor-pointer"
              >
                Use as Active Key
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Key Modal Overlay */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-forest/20 p-6 sm:p-8 max-w-md w-full space-y-6 shadow-2xl spade-cut-md">
            <div className="flex items-center justify-between border-b border-forest/10 pb-3">
              <h3 className="font-display text-xl font-bold text-forest flex items-center gap-2">
                <Key size={18} className="text-forest" />
                Generate New API Key
              </h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="text-forest/50 hover:text-forest font-mono text-sm cursor-pointer"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateKey} className="space-y-4">
              <div>
                <label className="block text-xs font-mono font-bold text-forest uppercase tracking-wider mb-1.5">
                  Key Name / Purpose
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Production Voice Gateway"
                  value={keyName}
                  onChange={(e) => setKeyName(e.target.value)}
                  className="w-full bg-sage-1 border border-forest/20 px-3.5 py-2.5 rounded-lg text-sm text-forest font-mono outline-none focus:border-forest"
                />
              </div>

              <div>
                <label className="block text-xs font-mono font-bold text-forest uppercase tracking-wider mb-1.5">
                  Subscription Tier
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'free', name: 'Free', limit: '3k / mo' },
                    { id: 'pro', name: 'Pro', limit: '300k / mo' },
                    { id: 'enterprise', name: 'Enterprise', limit: '30M / mo' },
                  ].map((t) => (
                    <button
                      type="button"
                      key={t.id}
                      onClick={() => setKeyTier(t.id)}
                      className={`p-3 rounded-lg border text-left font-mono transition-all cursor-pointer ${
                        keyTier === t.id
                          ? 'bg-forest text-white border-forest shadow-sm'
                          : 'bg-sage-1 border-forest/15 text-forest hover:border-forest/30'
                      }`}
                    >
                      <div className="text-xs font-bold capitalize">{t.name}</div>
                      <div className={`text-[10px] ${keyTier === t.id ? 'text-lemongrass' : 'text-forest/60'}`}>
                        {t.limit}
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-2 flex justify-end gap-3 border-t border-forest/10">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 rounded-lg bg-sage-1 text-forest font-mono text-xs font-bold hover:bg-sage-2 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating || !keyName.trim()}
                  className="px-5 py-2 rounded-lg bg-forest text-lemongrass font-mono text-xs font-bold hover:bg-forest-hover transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {creating ? 'Generating...' : 'Create API Key'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Keys Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-sage-2 text-forest border-b border-forest/10 font-bold">
            <tr>
              <th className="py-3 px-4">Key Name</th>
              <th className="py-3 px-4">Key ID</th>
              <th className="py-3 px-4">Masked Key</th>
              <th className="py-3 px-4">Tier</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Created</th>
              <th className="py-3 px-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-forest/5 text-forest/80">
            {keys.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-forest/50">
                  {loading ? 'Loading API keys...' : 'No API keys registered for this org. Click "Generate New API Key" above.'}
                </td>
              </tr>
            ) : (
              keys.map((k) => {
                const isActiveKey = activeApiKey && (activeApiKey === k.api_key || activeApiKey.includes(k.key_id));
                return (
                  <tr key={k.key_id} className={`hover:bg-sage-1/50 transition-colors ${isActiveKey ? 'bg-lemongrass/10' : ''}`}>
                    <td className="py-3 px-4 font-bold text-forest">
                      {k.name}
                      {isActiveKey && (
                        <span className="ml-2 px-2 py-0.5 rounded text-[9px] bg-forest text-lemongrass uppercase font-bold">
                          Selected Active
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-forest/60">{k.key_id}</td>
                    <td className="py-3 px-4 font-bold text-forest/80">{k.api_key}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-sage-2 text-forest border border-forest/15">
                        {k.tier}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      {k.is_active ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 border border-emerald-300">
                          Active
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-rose-100 text-rose-800 border border-rose-300">
                          Revoked
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-forest/60 whitespace-nowrap">
                      {new Date(k.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-right space-x-2 whitespace-nowrap">
                      {k.is_active && (
                        <button
                          onClick={() => handleRevokeKey(k.key_id)}
                          disabled={revokingId === k.key_id}
                          className="px-2.5 py-1 rounded bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold border border-rose-200 transition-colors cursor-pointer"
                        >
                          {revokingId === k.key_id ? 'Revoking...' : 'Revoke'}
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
}
