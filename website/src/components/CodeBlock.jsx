import React, { useState } from 'react';
import { Check, Copy, Terminal } from 'lucide-react';

function highlightCode(code, language) {
  if (!code) return '';

  const escapeHtml = (str) =>
    str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  if (language === 'json') {
    const jsonRegex = /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g;
    return code.replace(jsonRegex, (match) => {
      let cls = 'text-sky-300 font-bold';
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'text-emerald-300 font-semibold';
        } else {
          cls = 'text-amber-200 font-mono';
        }
      } else if (/true|false/.test(match)) {
        cls = 'text-pink-400 font-bold';
      } else if (/null/.test(match)) {
        cls = 'text-slate-400 italic';
      }
      return `<span class="${cls}">${escapeHtml(match)}</span>`;
    });
  }

  const keywordsSet = new Set([
    'import', 'from', 'as', 'def', 'class', 'return', 'with', 'open', 'print',
    'const', 'let', 'var', 'await', 'async', 'function', 'try', 'catch', 'if', 'else',
    'true', 'false', 'None', 'null', 'undefined', 'new', 'require',
    'curl', 'pip', 'npm', 'install', 'python', 'node', 'git', 'uvicorn'
  ]);

  // Single-pass tokenizer regex for Python, JS, TS, Bash
  const tokenRegex = /(#.*|\/\/.*)|("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)|(\b[a-zA-Z_]\w*\b)|(\b\d+\.?\d*\b)/g;

  let lastIndex = 0;
  let result = '';

  let match;
  while ((match = tokenRegex.exec(code)) !== null) {
    // Append plain text before match
    result += escapeHtml(code.slice(lastIndex, match.index));
    lastIndex = tokenRegex.lastIndex;

    const [fullMatch, comment, stringLiteral, identifier, number] = match;

    if (comment) {
      result += `<span class="text-slate-400 italic">${escapeHtml(comment)}</span>`;
    } else if (stringLiteral) {
      result += `<span class="text-amber-200">${escapeHtml(stringLiteral)}</span>`;
    } else if (identifier) {
      if (keywordsSet.has(identifier)) {
        result += `<span class="text-pink-400 font-bold">${escapeHtml(identifier)}</span>`;
      } else {
        result += escapeHtml(identifier);
      }
    } else if (number) {
      result += `<span class="text-sky-300 font-bold">${escapeHtml(number)}</span>`;
    } else {
      result += escapeHtml(fullMatch);
    }
  }

  // Append remaining text
  result += escapeHtml(code.slice(lastIndex));
  return result;
}

export default function CodeBlock({ code, language = 'python', title = '' }) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const highlightedHtml = highlightCode(code, language);

  return (
    <div className="rounded-2xl border border-forest/20 bg-forest text-white overflow-hidden shadow-spade spade-cut-sm font-mono text-xs">
      {/* Header bar */}
      <div className="flex items-center justify-between px-5 py-3 bg-[#0d2217] border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 mr-2">
            <span className="w-2.5 h-2.5 rounded-full bg-red-400/80 inline-block"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400/80 inline-block"></span>
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/80 inline-block"></span>
          </div>
          <Terminal size={14} className="text-lemongrass" />
          <span className="font-bold text-xs text-white/90 font-mono tracking-wide">{title || language}</span>
        </div>

        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white/90 hover:text-white transition-all cursor-pointer text-xs font-mono font-semibold"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check size={14} className="text-lemongrass" />
              <span className="text-lemongrass font-bold">Copied!</span>
            </>
          ) : (
            <>
              <Copy size={14} />
              <span>Copy Code</span>
            </>
          )}
        </button>
      </div>

      {/* Code content with single-pass syntax highlighting */}
      <div className="p-5 overflow-x-auto text-sage-1 leading-relaxed max-h-[520px] bg-[#0b1c13]">
        <pre className="font-mono text-xs">
          <code dangerouslySetInnerHTML={{ __html: highlightedHtml }} />
        </pre>
      </div>
    </div>
  );
}
