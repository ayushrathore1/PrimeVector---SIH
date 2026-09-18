import React, { useRef, useState, useCallback } from 'react';
import { Upload, FileAudio, X, CheckCircle2 } from 'lucide-react';

export default function AudioUploader({ onFileSelect, isProcessing }) {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileRef = useRef(null);

  const ACCEPTED = ['audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/mp4', 'audio/x-m4a', 'audio/webm', 'audio/x-wav'];
  const MAX_SIZE_MB = 25;

  const handleFile = useCallback((file) => {
    if (!file) return;

    if (!ACCEPTED.some(t => file.type.includes(t.split('/')[1])) && !file.name.match(/\.(wav|mp3|ogg|m4a|webm)$/i)) {
      alert('Unsupported format. Use WAV, MP3, OGG, M4A, or WebM.');
      return;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      alert(`File too large. Max ${MAX_SIZE_MB}MB.`);
      return;
    }

    setSelectedFile(file);
    onFileSelect(file);
  }, [onFileSelect]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    handleFile(file);
  }, [handleFile]);

  const clearFile = () => {
    setSelectedFile(null);
    if (fileRef.current) fileRef.current.value = '';
  };

  return (
    <div className="space-y-3">
      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        className={`relative cursor-pointer spade-cut-md border-2 border-dashed p-8 text-center transition-all duration-200 ${
          dragOver
            ? 'border-forest bg-lemongrass/20 scale-[1.01]'
            : selectedFile
            ? 'border-emerald-500 bg-emerald-50'
            : 'border-forest/20 bg-sage-1 hover:border-forest/40 hover:bg-sage-2'
        }`}
      >
        {selectedFile ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-12 h-12 rounded-full bg-emerald-100 border border-emerald-300 flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6 text-emerald-700" />
            </div>
            <div>
              <p className="font-mono text-sm text-forest font-bold">{selectedFile.name}</p>
              <p className="text-xs text-forest/70 mt-1">
                {(selectedFile.size / 1024).toFixed(1)} KB • {selectedFile.type || 'audio file'}
              </p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); clearFile(); }}
              className="flex items-center gap-1 px-3 py-1 rounded-md text-xs font-mono text-rose-700 hover:bg-rose-100 transition-colors"
            >
              <X size={12} /> Remove file
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className={`w-14 h-14 rounded-xl border flex items-center justify-center transition-colors ${
              dragOver ? 'bg-forest text-lemongrass border-forest' : 'bg-white border-forest/15 text-forest'
            }`}>
              <Upload className="w-6 h-6" />
            </div>
            <div>
              <p className="font-display text-base font-bold text-forest">
                <span className="text-forest underline">Click to upload audio</span> or drag and drop
              </p>
              <p className="text-xs text-forest/60 mt-1 font-mono">
                WAV, MP3, OGG, M4A, WebM • Max {MAX_SIZE_MB}MB
              </p>
            </div>
          </div>
        )}

        <input
          ref={fileRef}
          type="file"
          accept="audio/*,.wav,.mp3,.ogg,.m4a,.webm"
          className="hidden"
          onChange={(e) => handleFile(e.target.files?.[0])}
        />
      </div>
    </div>
  );
}
