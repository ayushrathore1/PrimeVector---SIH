import React, { useState } from 'react';
import { Check, Copy, Terminal } from 'lucide-react';

export default function CodeBlock({ code, language = 'python', title = '' }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-lg border border-obsidian-700 bg-obsidian-900 overflow-hidden shadow-card-glow font-mono-tech text-xs">
      <div className="flex items-center justify-between px-4 py-2.5 bg-obsidian-850 border-b border-obsidian-700">
        <div className="flex items-center gap-2 text-slate-400">
          <Terminal size={14} className="text-forensic-amber" />
          <span className="font-medium text-slate-300">{title || language}</span>
        </div>
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1.5 px-2 py-1 rounded bg-obsidian-800 hover:bg-obsidian-700 text-slate-400 hover:text-slate-200 transition-colors"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check size={13} className="text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy size={13} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="p-4 overflow-x-auto text-slate-300 leading-relaxed max-h-[480px]">
        <pre className="font-mono text-xs">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}
