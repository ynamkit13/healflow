import React, { useState, useEffect } from 'react';

export default function App() {
  const [signals, setSignals] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = () => {
    fetch('http://127.0.0.1:8000/api/signals')
      .then(res => res.json())
      .then(data => {
        setSignals(data);
        if (!selected && data.length > 0) setSelected(data[0]);
        else if (selected) setSelected(data.find(s => s.id === selected.id));
      });
  };

  useEffect(() => { load(); }, []);

  const handleHeal = async () => {
    setLoading(true);
    try {
      await fetch(`http://127.0.0.1:8000/api/signals/${selected.id}/heal`, { method: 'POST' });
      load();
    } finally {
      setLoading(false);
    }
  };

  // Logic to separate merchants by severity
  const criticalSignals = signals.filter(s => s.severity === 'high');
  const recentSignals = signals.filter(s => s.severity === 'low');

  return (
    <div className="flex h-screen bg-black text-white font-mono text-[12px]">
      {/* SIDEBAR */}
      <div className="w-72 border-r border-white/10 p-6 bg-zinc-950 overflow-y-auto">
        <div className="text-emerald-500 font-bold mb-6 italic">HEALFLOW</div>

        {/* LIVE SYSTEM STATUS */}
        <div className="mb-8 p-4 bg-emerald-500/5 border border-emerald-500/20 rounded">
          <div className="flex justify-between items-center text-[10px]">
            <span className="text-emerald-500 animate-pulse font-bold">● SYSTEM_ACTIVE</span>
            <span className="text-zinc-500">{criticalSignals.length} CRITICAL</span>
          </div>
        </div>
        
        {/* CRITICAL RADAR SECTION */}
        <div className="mb-10">
          <div className="text-[10px] text-zinc-600 font-black mb-4 tracking-[0.3em] uppercase">Critical_Radar</div>
          <div className="space-y-4">
            {criticalSignals.map(s => (
              <div key={s.id} onClick={() => setSelected(s)} 
                   className={`p-4 border border-white/5 cursor-pointer rounded transition-all ${selected?.id === s.id ? 'bg-emerald-500/10 border-emerald-500' : 'opacity-40 hover:opacity-100'}`}>
                <div className="font-bold uppercase tracking-tighter text-red-400">{s.merchant}</div>
                <div className="text-[9px] mt-1 text-zinc-500 uppercase flex justify-between">
                  <span>{s.status}</span>
                  <span className="text-red-600 font-bold">!!</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* RECENT SIGNALS SECTION */}
        <div>
          <div className="text-[10px] text-zinc-600 font-black mb-4 tracking-[0.3em] uppercase">Recent_Signals</div>
          <div className="space-y-4">
            {recentSignals.map(s => (
              <div key={s.id} onClick={() => setSelected(s)} 
                   className={`p-4 border border-white/5 cursor-pointer rounded transition-all ${selected?.id === s.id ? 'bg-emerald-500/10 border-emerald-500' : 'opacity-40 hover:opacity-100'}`}>
                <div className="font-bold uppercase tracking-tighter">{s.merchant}</div>
                <div className="text-[9px] mt-1 text-zinc-500 uppercase">{s.status}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* MAIN VIEWPORT */}
      <div className="flex-1 p-16 overflow-y-auto">
        {selected ? (
          <div className="max-w-3xl space-y-10">
            <h1 className="text-7xl font-black uppercase italic tracking-tighter">{selected.merchant}</h1>
            <p className="text-zinc-500 text-[11px] uppercase tracking-widest">{selected.description}</p>

            <div className="bg-zinc-900/50 p-8 border border-white/10 rounded">
              <h3 className="text-emerald-500/50 text-[10px] uppercase mb-4 font-bold">Root_Cause</h3>
              <p className="text-[13px] leading-relaxed">
                {selected.ai_data?.analysis?.root_cause ?? (loading ? "AI_ANALYZING..." : "Awaiting Protocol Initiation...")}
              </p>
            </div>

            {/* AI REASONING ORDA LOOP */}
            {selected.ai_data?.orda_loop && (
              <div className="grid grid-cols-1 gap-2 text-[10px]">
                <div className="p-4 border border-white/5 opacity-60 uppercase font-bold text-emerald-500/70 tracking-widest">Observe: {selected.ai_data.orda_loop.observe}</div>
                <div className="p-4 border border-white/5 opacity-60 uppercase font-bold text-emerald-500/70 tracking-widest">Reason: {selected.ai_data.orda_loop.reason}</div>
                <div className="p-4 border border-white/5 opacity-60 uppercase font-bold text-emerald-500/70 tracking-widest">Decide: {selected.ai_data.orda_loop.decide}</div>
                <div className="p-4 border border-emerald-500/50 text-emerald-500 font-black tracking-widest underline">Act: {selected.ai_data.orda_loop.act}</div>
              </div>
            )}

            <button onClick={handleHeal} disabled={selected.status !== 'Pending' || loading} 
                    className="w-full py-10 font-black border border-white uppercase tracking-[1em] hover:bg-emerald-500 hover:text-white transition-all">
              {loading ? 'REASONING...' : (selected.status === 'Pending' ? 'Initiate_Heal' : 'Signal_Healed')}
            </button>
          </div>
        ) : <div className="h-full flex items-center justify-center italic opacity-20">SELECT_SIGNAL</div>}
      </div>
    </div>
  );
}