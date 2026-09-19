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
    <div className="rounded-xl border border-forest/20 bg-forest text-white overflow-hidden shadow-spade spade-cut-sm font-mono text-xs">
      <div className="flex items-center justify-between px-4 py-2.5 bg-forest-dark border-b border-white/10">
        <div className="flex items-center gap-2">
          <Terminal size={14} className="text-lemongrass" />
          <span className="font-bold text-xs text-white/90 font-mono tracking-wide">{title || language}</span>
        </div>
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white/80 hover:text-white transition-colors cursor-pointer text-xs font-mono font-semibold"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check size={13} className="text-lemongrass" />
              <span className="text-lemongrass">Copied</span>
            </>
          ) : (
            <>
              <Copy size={13} />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="p-4 overflow-x-auto text-sage-1 leading-relaxed max-h-[480px]">
        <pre className="font-mono text-xs">
          <code>{code}</code>
        </pre>
      </div>
    </div>
  );
}

