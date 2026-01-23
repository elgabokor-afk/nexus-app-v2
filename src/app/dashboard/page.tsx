'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import SignalCard from '@/components/SignalCard';
import { Zap, Activity } from 'lucide-react';
import PaperBotWidget from '@/components/PaperBotWidget';
import dynamic from 'next/dynamic';

const SmartChart = dynamic(
    () => import('@/components/SmartChart').then((mod) => mod.SmartChart),
    {
        ssr: false,
        loading: () => <div className="w-full h-full bg-[#050505] animate-pulse flex items-center justify-center text-gray-800">Initializing Chart Engine...</div>
    }
);

declare global {
    interface Window {
        TradingView: any;
    }
}

interface Signal {
    id: number;
    symbol: string;
    price: number;
    rsi: number;
    signal_type: string;
    confidence: number;
    timestamp: string;
    stop_loss?: number;
    take_profit?: number;
}

// ... (imports remain same, just ensure structure)
export default function Dashboard() {
    const [signals, setSignals] = useState<Signal[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true); // Default open on desktop
    const [mounted, setMounted] = useState(false);

    const handleViewChart = (symbol: string) => {
        const sig = signals.find(s => s.symbol === symbol);
        if (sig) {
            setSelectedSignal(sig);
            if (window.innerWidth < 1024) {
                const chartElement = document.getElementById('main-chart-area');
                chartElement?.scrollIntoView({ behavior: 'smooth' });
            }
        }
    };

    const fetchSignals = async () => {
        const { data, error } = await supabase
            .from('market_signals')
            .select('*')
            .order('timestamp', { ascending: false })
            .limit(50);

        if (error) console.error('Error fetching signals:', error);
        else {
            setSignals(data || []);
            if (data && data.length > 0 && !selectedSignal) {
                setSelectedSignal(data[0]);
            }
        }
        setLoading(false);
    };

    useEffect(() => {
        setMounted(true);
        fetchSignals();

        // Close sidebar by default on smaller screens
        if (window.innerWidth < 1280) setIsSidebarOpen(false);

        const channel = supabase
            .channel('realtime signals')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'market_signals' }, (payload: any) => {
                const newSignal = payload.new as Signal;
                setSignals((prev) => {
                    const exists = prev.find(s => s.id === newSignal.id);
                    if (exists) return prev;
                    return [newSignal, ...prev].slice(0, 100);
                });
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    if (!mounted) return (
        <div className="h-screen bg-[#050505] flex flex-col items-center justify-center text-[#00ffa3] font-mono">
            <div className="w-12 h-12 border-2 border-[#00ffa3] border-t-transparent rounded-full animate-spin mb-4 shadow-[0_0_15px_#00ffa3]"></div>
            <span className="animate-pulse">BOOTING NEXUS TERMINAL...</span>
        </div>
    );

    return (
        <div className="h-screen bg-[#050505] text-white font-sans overflow-hidden flex flex-col">

            {/* TOP BAR / HEADER */}
            <header className="h-20 border-b border-white/5 flex items-center justify-between px-6 bg-[#0a0a0c]/80 backdrop-blur-2xl z-[60] relative">
                <div className="flex items-center gap-6">
                    {/* Hamburger Toggle */}
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="p-3 hover:bg-white/5 rounded-2xl transition-all active:scale-95 group border border-white/5"
                    >
                        <div className="space-y-1.5">
                            <div className={`h-0.5 w-5 bg-gray-400 group-hover:bg-[#00ffa3] transition-all ${isSidebarOpen ? 'rotate-45 translate-y-2' : ''}`}></div>
                            <div className={`h-0.5 w-5 bg-gray-400 group-hover:bg-[#00ffa3] transition-all ${isSidebarOpen ? 'opacity-0' : ''}`}></div>
                            <div className={`h-0.5 w-5 bg-gray-400 group-hover:bg-[#00ffa3] transition-all ${isSidebarOpen ? '-rotate-45 -translate-y-1' : ''}`}></div>
                        </div>
                    </button>

                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#00ffa3] to-[#00ce82] flex items-center justify-center text-black shadow-[0_0_30px_rgba(0,255,163,0.3)] border border-[#00ffa3]/20">
                            <Zap size={20} fill="currentColor" />
                        </div>
                        <div className="hidden sm:block">
                            <span className="font-black tracking-tighter text-xl">NEXUS<span className="text-[#00ffa3]">AI</span></span>
                            <p className="text-[10px] text-gray-500 font-bold tracking-widest leading-none">TERMINAL V2</p>
                        </div>
                    </div>

                    <div className="h-10 w-px bg-white/5 mx-2 hidden md:block"></div>

                    {/* Selected Symbol Display */}
                    {selectedSignal && (
                        <div className="hidden md:flex items-center gap-5 animate-in fade-in slide-in-from-left-6 duration-700">
                            <div className="flex items-center gap-3 bg-white/[0.03] border border-white/5 px-4 py-2 rounded-2xl">
                                <img
                                    src={`https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/${selectedSignal.symbol.split('/')[0].toLowerCase()}.png`}
                                    alt={selectedSignal.symbol}
                                    className="w-10 h-10 object-contain drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]"
                                    onError={(e) => (e.target as HTMLImageElement).style.display = 'none'}
                                />
                                <div>
                                    <h2 className="text-xl font-black tracking-tighter leading-none">{selectedSignal.symbol}</h2>
                                    <p className="text-[11px] text-[#00ffa3] font-mono mt-0.5 font-bold tracking-tighter">${selectedSignal.price.toLocaleString()}</p>
                                </div>
                            </div>

                            <div className="flex flex-col gap-1.5">
                                <span className="text-[9px] text-gray-500 uppercase tracking-[0.2em] font-black">AI Signal Strength</span>
                                <div className="flex items-center gap-3">
                                    <div className="w-32 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                                        <div
                                            className="h-full bg-gradient-to-r from-[#00ffa3] to-[#00ce82] shadow-[0_0_15px_rgba(0,255,163,0.4)] transition-all duration-1000 ease-out"
                                            style={{ width: `${selectedSignal.confidence}%` }}
                                        />
                                    </div>
                                    <span className="text-xs font-black text-[#00ffa3]">{selectedSignal.confidence}%</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-4">
                    <div className="hidden lg:flex items-center gap-3 px-4 py-2 rounded-2xl bg-white/[0.03] border border-white/5 text-[#00ffa3]">
                        <span className="w-2 h-2 rounded-full bg-current animate-pulse shadow-[0_0_10px_currentColor]"></span>
                        <span className="text-[10px] font-black tracking-widest uppercase">Streaming Real-time Data</span>
                    </div>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden relative">

                {/* SIDEBAR NAVIGATION - Drawer style */}
                <aside className={`
                    fixed md:relative inset-y-0 left-0 w-72 bg-[#0a0a0c]/95 border-r border-white/5 flex flex-col z-50 transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]
                    ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:-ml-72'}
                    backdrop-blur-3xl shadow-2xl
                `}>
                    <nav className="flex-1 p-6 space-y-2 mt-4">
                        <div className="px-4 py-2 text-[10px] font-black text-gray-600 uppercase tracking-[0.3em] mb-4">Operations</div>
                        <button className="w-full flex items-center justify-between px-5 py-4 bg-gradient-to-r from-[#00ffa3]/10 to-transparent text-[#00ffa3] rounded-2xl border border-[#00ffa3]/20 shadow-[0_0_20px_-5px_rgba(0,255,163,0.2)] group">
                            <div className="flex items-center gap-4">
                                <Activity size={18} className="animate-pulse" />
                                <span className="text-sm font-black tracking-tight">AI TERMINAL</span>
                            </div>
                            <Zap size={14} fill="currentColor" />
                        </button>
                        <button className="w-full flex items-center gap-4 px-5 py-4 text-gray-500 hover:text-white hover:bg-white/[0.03] rounded-2xl transition-all duration-300 border border-transparent hover:border-white/5">
                            <Zap size={18} />
                            <span className="text-sm font-bold tracking-tight">PAPER BOT ENGINE</span>
                        </button>
                        <button className="w-full flex items-center gap-4 px-5 py-4 text-gray-500 hover:text-white hover:bg-white/[0.03] rounded-2xl transition-all duration-300 border border-transparent hover:border-white/5">
                            <Activity size={18} />
                            <span className="text-sm font-bold tracking-tight">ALGORITHMIC LOGS</span>
                        </button>
                    </nav>

                    <div className="p-6">
                        <div className="p-5 rounded-3xl bg-white/[0.03] border border-white/5 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-24 h-24 bg-[#00ffa3]/5 rounded-full blur-3xl -mr-12 -mt-12 transition-all group-hover:bg-[#00ffa3]/10"></div>
                            <p className="text-[10px] text-gray-500 uppercase tracking-widest font-black mb-2 flex items-center gap-2">
                                <span className="w-1.5 h-1.5 rounded-full bg-[#00ffa3] animate-ping"></span>
                                Node Status
                            </p>
                            <div className="flex items-end justify-between">
                                <span className="text-sm font-black text-white">OPTIMIZED (v2.2)</span>
                                <span className="text-[9px] font-mono text-gray-600 uppercase">99.9% Uptime</span>
                            </div>
                        </div>
                    </div>
                </aside>

                {/* Backdrop for sidebar */}
                {isSidebarOpen && (
                    <div
                        className="fixed inset-0 bg-black/60 backdrop-blur-md z-40 md:hidden animate-in fade-in duration-500"
                        onClick={() => setIsSidebarOpen(false)}
                    />
                )}

                {/* MAIN DASHBOARD CONTENT */}
                <main className="flex-1 flex flex-col relative overflow-hidden bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-[#1a1a2e] via-[#050505] to-[#050505]">

                    {/* Background Pattern */}
                    <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }}></div>

                    <div className="flex-1 p-4 lg:p-8 grid grid-cols-1 lg:grid-cols-12 gap-8 overflow-y-auto lg:overflow-hidden z-20 custom-scrollbar">

                        {/* COL 1: ADVANCED SIGNALS (4 Columns for more space) */}
                        <div className="lg:col-span-4 flex flex-col gap-6 overflow-hidden min-h-[500px] lg:min-h-0 bg-black/20 backdrop-blur-md rounded-[2.5rem] border border-white/5 p-6 shadow-2xl">
                            <div className="flex items-center justify-between px-2">
                                <h3 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.4em]">Algorithmic Pulse</h3>
                                <div className="flex items-center gap-2 bg-[#00ffa3]/10 px-3 py-1 rounded-full border border-[#00ffa3]/20">
                                    <span className="text-[10px] text-[#00ffa3] font-black font-mono">{signals.length} ANALYZED</span>
                                </div>
                            </div>
                            <div className="flex-1 overflow-y-auto space-y-4 pr-3 custom-scrollbar-wide pb-4">
                                {loading ? (
                                    <div className="space-y-4">
                                        {[1, 2, 3, 4].map(i => <div key={i} className="h-32 rounded-3xl bg-white/5 animate-pulse border border-white/5"></div>)}
                                    </div>
                                ) : (
                                    signals.map((signal) => (
                                        <SignalCard
                                            key={signal.id}
                                            {...signal}
                                            onViewChart={handleViewChart}
                                            compact={true}
                                        />
                                    ))
                                )}
                            </div>
                        </div>

                        {/* COL 2: MAIN ENGINE (Rest for Chart & Bot) */}
                        <div id="main-chart-area" className="lg:col-span-8 flex flex-col gap-8">

                            {/* Chart Stage */}
                            <div className="flex-1 min-h-[500px] rounded-[3rem] border border-white/10 bg-[#0a0a0c]/40 backdrop-blur-3xl relative overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)] flex flex-col group/chart">
                                <div className="flex-1 w-full h-full relative">
                                    <div className="absolute inset-0 bg-gradient-to-b from-[#00ffa3]/5 to-transparent pointer-events-none"></div>
                                    <SmartChart
                                        symbol={selectedSignal?.symbol || 'BTC/USD'}
                                        signalData={selectedSignal ? {
                                            entry: selectedSignal.price,
                                            stop_loss: selectedSignal.stop_loss,
                                            take_profit: selectedSignal.take_profit,
                                            confidence: selectedSignal.confidence,
                                            signal_type: selectedSignal.signal_type
                                        } : null}
                                    />
                                </div>
                            </div>

                            {/* Secondary Engine: Paper Bot */}
                            <div className="h-[320px] lg:h-[380px] rounded-[3rem] border border-white/10 bg-[#0a0a0c]/60 backdrop-blur-2xl overflow-hidden shadow-2xl relative">
                                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#00ffa3]/20 to-transparent"></div>
                                <PaperBotWidget />
                            </div>
                        </div>

                    </div>
                </main>
            </div>
        </div>
    );
}

