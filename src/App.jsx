import React, { useState, useEffect } from 'react';

export default function App() {
  const [signals, setSignals] = useState([]); // Now using State instead of importing JSON
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [status, setStatus] = useState('pending');

  // --- FETCH DATA FROM FASTAPI ---
  useEffect(() => {
    const getSignals = async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/signals');
        const data = await response.json();
        setSignals(data);
        setLoading(false);
      } catch (err) {
        console.error("FastAPI Error: Is your uvicorn server running?", err);
        setLoading(false);
      }
    };
    getSignals();
  }, []);

  // Sort signals: Critical failures first, then by frequency
  const sortedSignals = [...signals].sort((a, b) => {
    const isACritical = a.description.toLowerCase().includes('checkout');
    const isBCritical = b.description.toLowerCase().includes('checkout');
    if (isACritical && !isBCritical) return -1;
    if (!isACritical && isBCritical) return 1;
    return b.frequency - a.frequency;
  });

  // --- UPDATE STATUS ON FASTAPI ---
  const handleHeal = async () => {
    if (!selected) return;
    setStatus('healing');

    try {
      // Tell FastAPI to update this signal
      await fetch(`http://127.0.0.1:8000/api/signals/${selected.id}`, {
        method: 'POST'
      });

      // Simulation delay for visual effect
      setTimeout(async () => {
        setStatus('healed');
        // Refresh the list from the server to show it's updated
        const response = await fetch('http://127.0.0.1:8000/api/signals');
        const refreshedData = await response.json();
        setSignals(refreshedData);
      }, 2000);
    } catch (err) {
      console.error("Heal failed:", err);
      setStatus('pending');
    }
  };

  if (loading) return (
    <div className="h-screen bg-black flex items-center justify-center font-mono text-emerald-500 italic">
    {">"} ESTABLISHING_SECURE_API_LINK...
  </div>
  );

  return (
    <div className="flex h-screen bg-black text-white overflow-hidden font-mono">
      
      {/* Sidebar */}
      <div className="w-80 border-r border-white/10 flex flex-col bg-black">
        <div className="p-6 border-b border-white/10">
          <h1 className="text-emerald-500 font-bold tracking-[0.3em] text-[10px]">HEALFLOW // SYSTEM_RADAR</h1>
        </div>
        <div className="flex-1 overflow-y-auto">
          {sortedSignals.map(s => (
            <div 
              key={s.id} 
              onClick={() => {setSelected(s); setStatus('pending');}} 
              className={`p-5 border-b border-white/5 cursor-pointer transition-all hover:bg-white/5 ${selected?.id === s.id ? 'bg-white/5 border-l-2 border-emerald-500' : ''}`}
            >
              <div className="flex justify-between items-center mb-2">
                <span className={`text-[9px] px-2 py-0.5 rounded-sm font-bold ${s.description.toLowerCase().includes('checkout') ? 'bg-red-900/40 text-red-500 border border-red-500/50' : 'bg-zinc-800 text-zinc-400'}`}>
                  {s.status === 'healed' ? 'REPAIRED' : (s.description.toLowerCase().includes('checkout') ? 'CRITICAL_FAIL' : 'SIGNAL_IDLE')}
                </span>
                <span className="text-[10px] text-zinc-600">FRQ_{s.frequency}</span>
              </div>
              <div className="font-bold text-zinc-300 tracking-tight">{s.merchant}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Panel */}
      <div className="flex-1 p-12 bg-black border-l border-white/10">
        {selected ? (
          <div className="max-w-4xl space-y-12">
            <header className="border-b border-white/10 pb-8">
              <h2 className="text-6xl font-black tracking-tighter text-white uppercase italic">
                {selected.merchant}
              </h2>
              <p className="text-zinc-500 mt-4 text-sm leading-relaxed uppercase tracking-widest">{selected.description}</p>
            </header>

            <div className="grid grid-cols-2 gap-8">
              <div className="bg-zinc-900/30 p-6 rounded border border-white/10">
                <h3 className="text-[9px] font-bold text-zinc-600 uppercase mb-4 tracking-widest">TELEMETRY_LOG</h3>
                <pre className="text-[11px] text-emerald-500/70 font-mono leading-tight uppercase">
                   {/* Fallback metadata if your FastAPI doesn't provide it yet */}
                  {JSON.stringify(selected.metadata || { "node": "INTERNAL", "port": 8000 }, null, 2)}
                </pre>
              </div>

              <div className="bg-zinc-900/30 p-6 rounded border border-white/10">
                <h3 className="text-[9px] font-bold text-emerald-500/50 uppercase mb-4 tracking-widest">AGENT_REASONING</h3>
                <div className="text-[11px] text-emerald-500 space-y-3">
                  <p className={status === 'pending' ? 'animate-pulse' : ''}>
                    {status === 'pending' ? '> ANALYZING_DELTA...' : '> AUTO_PATCH_SUCCESS.'}
                  </p>
                  <p className="text-zinc-600 italic mt-4">STATUS: {status.toUpperCase()}</p>
                </div>
              </div>
            </div>

            <button 
              onClick={handleHeal} 
              disabled={status !== 'pending' || selected.status === 'healed'} 
              className={`w-full py-6 rounded-none font-bold uppercase tracking-[0.5em] transition-all border ${
                status === 'pending' && selected.status !== 'healed'
                  ? 'bg-white text-black border-white hover:bg-transparent hover:text-white' 
                  : 'bg-transparent text-zinc-700 border-white/10'
              }`}
            >
              {selected.status === 'healed' ? 'NODE_SECURED' : (status === 'pending' ? 'EXECUTE_FIX' : 'PROCESSING_PATCH...')}
            </button>
          </div>
        ) : (
          <div className="h-full flex flex-col items-center justify-center space-y-4">
            <div className="w-8 h-8 border border-emerald-500/20 rounded-full flex items-center justify-center animate-pulse">
               <div className="w-2 h-2 bg-emerald-500 rounded-full"></div>
            </div>
            <p className="text-[10px] uppercase tracking-[0.8em] text-zinc-800">Awaiting_Input_Signal</p>
          </div>
        )}
      </div>
    </div>
  );
}