import React, { useState, useEffect, useRef } from 'react';

export default function App() {
  const [signals, setSignals] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Prevents the "Mumbai Jump" by locking initial selection
  const isInitialLoad = useRef(true);

  // Decoupled selection logic to prevent UI flickering during polling
  const selected = signals.find(s => s.id === selectedId) || null;

  const load = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/signals');
      const data = await res.json();
      setSignals(data);
      
      // Only auto-select the first item on the very first load
      if (isInitialLoad.current && data.length > 0) {
        setSelectedId(data[0].id);
        isInitialLoad.current = false; 
      }
    } catch (err) {
      console.error("Sync Error:", err);
    }
  };

  // Background Polling - Every 3 seconds
  useEffect(() => { 
    load(); 
    const interval = setInterval(load, 3000); 
    return () => clearInterval(interval);
  }, []); 

  const handleAction = async (action) => {
    setLoading(true);
    try {
      await fetch(`http://127.0.0.1:8000/api/signals/${selectedId}/${action}`, { method: 'POST' });
      await load(); 
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (vote) => {
    try {
      await fetch(`http://127.0.0.1:8000/api/signals/${selectedId}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ vote })
      });
      load(); 
    } catch (err) {
      console.error("Feedback failed:", err);
    }
  };

  const criticalSignals = signals.filter(s => s.severity === 'high');
  const recentSignals = signals.filter(s => s.severity === 'low');

  return (
    <div className="flex h-screen bg-black text-white font-mono text-[12px] overflow-hidden">
      {/* SIDEBAR */}
      <div className="w-72 border-r border-white/10 p-6 bg-zinc-950 overflow-y-auto">
        <div className="text-emerald-500 font-bold mb-6 italic tracking-tighter uppercase">HealFlow_v2</div>

        <div className="mb-8 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded">
          <div className="flex justify-between items-center text-[10px]">
            <span className="text-emerald-500 animate-pulse font-bold">● SYSTEM_LIVE</span>
            <span className="text-zinc-500">{criticalSignals.length} ALERT</span>
          </div>
        </div>
        
        {/* SIDEBAR SECTIONS */}
        {[["Critical_Radar", criticalSignals], ["Recent_Signals", recentSignals]].map(([title, list]) => (
          <div key={title} className="mb-10">
            <div className="text-[10px] text-zinc-600 font-black mb-4 tracking-[0.3em] uppercase">{title}</div>
            <div className="space-y-3">
              {list.map(s => (
                <div key={s.id} onClick={() => setSelectedId(s.id)} 
                     className={`p-4 border border-white/5 cursor-pointer rounded transition-all duration-300 ${selectedId === s.id ? 'bg-emerald-500/10 border-emerald-500' : 'opacity-40 hover:opacity-100'}`}>
                  <div className={`font-bold uppercase tracking-tighter ${s.status === 'Engineer_Assigned' ? 'text-orange-500' : s.severity === 'high' ? 'text-red-400' : 'text-white'}`}>{s.merchant}</div>
                  <div className="text-[9px] mt-1 text-zinc-500 uppercase">{s.status.replace('_', ' ')}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* MAIN VIEWPORT */}
      <div className="flex-1 p-16 overflow-y-auto bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-zinc-900/20 via-black to-black">
        {selected ? (
          <div className="max-w-3xl space-y-10">
            <div className="space-y-2">
                <span className={`text-[10px] px-2 py-1 rounded border ${selected.severity === 'high' ? 'border-red-500 text-red-500' : 'border-zinc-500 text-zinc-500'}`}>{selected.severity.toUpperCase()}</span>
                <h1 className="text-7xl font-black uppercase italic tracking-tighter">{selected.merchant}</h1>
                <p className="text-zinc-500 text-[11px] uppercase tracking-widest">{selected.description}</p>
            </div>

            <div className="bg-zinc-900/50 p-8 border border-white/10 rounded backdrop-blur-sm">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-emerald-500/50 text-[10px] uppercase font-bold tracking-widest">Diagnostic_Report</h3>
                {/* RAG MEMORY BADGE */}
                {selected.ai_data?.using_memory && (
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></span>
                    <span className="text-[9px] text-emerald-500 font-bold uppercase tracking-widest">Memory_Retrieved</span>
                  </div>
                )}
              </div>
              <p className="text-[13px] leading-relaxed">
                {selected.ai_data?.analysis?.root_cause ?? (loading ? "CONSULTING_HISTORICAL_SOLUTIONS..." : "Awaiting Protocol Initiation...")}
              </p>
            </div>

            {selected.ai_data?.orda_loop && (
              <div className="grid grid-cols-1 gap-2 text-[10px]">
                {Object.entries(selected.ai_data.orda_loop).map(([key, value]) => (
                  <div key={key} className={`p-4 border border-white/5 uppercase font-bold tracking-widest ${key === 'act' ? 'text-emerald-500 border-emerald-500/50 bg-emerald-500/5' : 'opacity-60 text-emerald-500/70'}`}>
                    {key}: {value}
                  </div>
                ))}
              </div>
            )}

            {/* ACTION UI */}
            <div className="pt-4">
              {selected.status === 'Awaiting_Approval' ? (
                <div className="flex gap-4">
                  <button onClick={() => handleAction('accept')} disabled={loading}
                          className="flex-1 py-10 font-black border border-emerald-500 bg-emerald-500/20 text-emerald-500 uppercase tracking-[0.5em] hover:bg-emerald-500 hover:text-white transition-all">
                    {loading ? 'EXECUTING...' : 'Accept_Protocol'}
                  </button>
                  <button onClick={() => handleAction('reject')} disabled={loading}
                          className="flex-1 py-10 font-black border border-red-500 text-red-500 uppercase tracking-[0.5em] hover:bg-red-500 hover:text-white transition-all">
                    Reject_&_Escalate
                  </button>
                </div>
              ) : selected.status === 'Engineer_Assigned' ? (
                <div className="w-full py-10 text-center font-black border border-orange-500/30 text-orange-500 uppercase tracking-[0.5em] bg-orange-500/5 rounded">
                  Escalated_to_L2_Engineer
                </div>
              ) : selected.status === 'Healed' ? (
                <div className="w-full space-y-4">
                  <div className="w-full py-10 text-center font-black border border-emerald-500 text-emerald-500 uppercase tracking-[0.5em] bg-emerald-500/10 rounded">
                    Signal_Resolved
                  </div>
                  
                  {/* Feedback Mechanism for Adaptation Loop */}
                  <div className="flex items-center justify-between p-4 border border-white/5 bg-zinc-900/30 rounded">
                    <span className="text-[10px] text-zinc-500 uppercase font-bold">Rate AI Outcome:</span>
                    <div className="flex gap-4">
                      <button 
                        onClick={() => handleFeedback('positive')}
                        className={`px-4 py-2 border text-[10px] transition-all ${selected.feedback === 'positive' ? 'bg-emerald-500 border-emerald-500 text-black' : 'border-white/20 hover:border-emerald-500 text-emerald-500'}`}
                      >
                        👍 Correct
                      </button>
                      <button 
                        onClick={() => handleFeedback('negative')}
                        className={`px-4 py-2 border text-[10px] transition-all ${selected.feedback === 'negative' ? 'bg-red-500 border-red-500 text-black' : 'border-white/20 hover:border-red-500 text-red-500'}`}
                      >
                        👎 Refine
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <button onClick={() => handleAction('heal')} disabled={loading} 
                        className="w-full py-10 font-black border border-white uppercase tracking-[1em] hover:bg-emerald-500 hover:text-white transition-all">
                  {loading ? 'AI_REASONING...' : 'Initiate_Heal'}
                </button>
              )}
            </div>
          </div>
        ) : <div className="h-full flex items-center justify-center italic opacity-20 tracking-[1em]">SYSTEM_STANDBY</div>}
      </div>
    </div>
  );
}