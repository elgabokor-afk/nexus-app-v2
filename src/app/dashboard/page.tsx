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
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [mounted, setMounted] = useState(false);

    const handleViewChart = (symbol: string) => {
        const sig = signals.find(s => s.symbol === symbol);
        if (sig) {
            setSelectedSignal(sig);
            // On mobile, we might want to scroll to the chart when a signal is selected
            if (window.innerWidth < 768) {
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
        <div className="h-screen bg-[#050505] text-white font-sans overflow-hidden flex flex-col md:flex-row">

            {/* MOBILE HEADER */}
            <div className="md:hidden h-14 border-b border-white/5 bg-[#0a0a0c] flex items-center justify-between px-4 z-[60]">
                <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-gradient-to-br from-[#00ffa3] to-[#00ce82] flex items-center justify-center text-black">
                        <Zap size={14} fill="currentColor" />
                    </div>
                    <span className="font-bold text-sm tracking-wide">NEXUS<span className="text-[#00ffa3]">AI</span></span>
                </div>
                <button
                    onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                    className="p-2 text-gray-400 hover:text-white transition-colors"
                >
                    <Activity size={20} />
                </button>
            </div>

            {/* SIDEBAR NAVIGATION - Responsive */}
            <aside className={`
                fixed inset-y-0 left-0 w-64 border-r border-white/5 bg-[#0a0a0c] flex flex-col z-50 transition-transform duration-300 ease-in-out
                ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0 md:relative md:flex'}
            `}>
                {/* Logo Area (Hidden on Mobile Header) */}
                <div className="hidden md:flex h-16 items-center px-6 border-b border-white/5">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00ffa3] to-[#00ce82] flex items-center justify-center text-black shadow-[0_0_20px_rgba(0,255,163,0.3)]">
                            <Zap size={18} fill="currentColor" />
                        </div>
                        <span className="font-bold tracking-wide text-lg">NEXUS<span className="text-[#00ffa3]">AI</span></span>
                    </div>
                </div>

                <nav className="flex-1 p-4 space-y-1">
                    <div className="px-3 py-2 text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Platform</div>
                    <button className="w-full flex items-center gap-3 px-3 py-2.5 bg-[#00ffa3]/10 text-[#00ffa3] rounded-lg border border-[#00ffa3]/20">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#00ffa3] shadow-[0_0_10px_#00ffa3]"></div>
                        <span className="text-sm font-medium">Terminal</span>
                    </button>
                    <button className="w-full flex items-center gap-3 px-3 py-2.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors group">
                        <div className="w-1.5 h-1.5 rounded-full bg-gray-600 group-hover:bg-gray-400"></div>
                        <span className="text-sm font-medium">Paper Bot</span>
                    </button>
                    <button className="w-full flex items-center gap-3 px-3 py-2.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors group">
                        <div className="w-1.5 h-1.5 rounded-full bg-gray-600 group-hover:bg-gray-400"></div>
                        <span className="text-sm font-medium">Risk Settings</span>
                    </button>
                </nav>

                <div className="p-4 border-t border-white/5">
                    <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                        <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">System Node</p>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-[#00ffa3] animate-pulse"></div>
                            <span className="text-xs font-bold text-[#00ffa3]">ACTIVE (v2.1)</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Backdrop for mobile sidebar */}
            {isSidebarOpen && (
                <div
                    className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
                    onClick={() => setIsSidebarOpen(false)}
                />
            )}

            {/* MAIN CONTENT AREA */}
            <main className="flex-1 flex flex-col relative overflow-hidden bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-[#1a1a2e] via-[#050505] to-[#050505]">

                {/* Top Bar - REDESIGNED with selected symbol info */}
                <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[#0a0a0c]/50 backdrop-blur-md z-30">
                    <div className="flex items-center gap-4">
                        {selectedSignal ? (
                            <div className="flex items-center gap-4 animate-in fade-in slide-in-from-left-4 duration-500">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 rounded-full bg-[#00ffa3]/10 border border-[#00ffa3]/20 flex items-center justify-center text-[#00ffa3] font-bold text-xs">
                                        {selectedSignal.symbol.split('/')[0]}
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-bold tracking-tighter leading-none">{selectedSignal.symbol}</h2>
                                        <p className="text-[10px] text-gray-500 font-mono mt-0.5">PRICE: ${selectedSignal.price.toLocaleString()}</p>
                                    </div>
                                </div>
                                <div className="h-8 w-px bg-white/10 hidden sm:block"></div>
                                <div className="hidden sm:flex flex-col">
                                    <span className="text-[8px] text-gray-500 uppercase tracking-widest font-bold">AI Signal Confidence</span>
                                    <div className="flex items-center gap-2 mt-0.5">
                                        <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/5">
                                            <div
                                                className="h-full bg-gradient-to-r from-[#00ffa3] to-[#00ce82] shadow-[0_0_10px_rgba(0,255,163,0.5)] transition-all duration-1000"
                                                style={{ width: `${selectedSignal.confidence}%` }}
                                            />
                                        </div>
                                        <span className="text-xs font-bold text-[#00ffa3]">{selectedSignal.confidence}%</span>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <h2 className="text-sm font-medium text-gray-400">Awaiting Signal...</h2>
                        )}
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#00ffa3]/10 border border-[#00ffa3]/20 text-[#00ffa3]">
                            <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
                            <span className="text-[10px] font-bold tracking-widest">LIVE DATA CONNECTED</span>
                        </div>
                        <div className="w-8 h-8 rounded-full border border-white/10 bg-white/5 flex items-center justify-center text-gray-400">
                            <Activity size={14} />
                        </div>
                    </div>
                </header>

                {/* Dashboard Grid - RESPONSIVE */}
                <div className="flex-1 overflow-y-auto md:overflow-hidden p-4 md:p-6 grid grid-cols-1 md:grid-cols-12 gap-6 custom-scrollbar">

                    {/* COL 1: SIGNALS (Top on mobile, Left on desktop) */}
                    <div className="order-2 md:order-1 md:col-span-3 flex flex-col gap-4 overflow-hidden min-h-[400px] md:min-h-0">
                        <div className="flex items-center justify-between px-1">
                            <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em]">Signal Pulse</h3>
                            <span className="text-[10px] text-[#00ffa3] font-mono bg-[#00ffa3]/10 px-2 py-0.5 rounded border border-[#00ffa3]/20">{signals.length} Active</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar pb-6">
                            {loading ? (
                                <div className="space-y-3">
                                    {[1, 2, 3, 4, 5].map(i => <div key={i} className="h-20 rounded-xl bg-white/5 animate-pulse border border-white/5"></div>)}
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

                    {/* COL 2: CHART (Middle) */}
                    <div id="main-chart-area" className="order-1 md:order-2 md:col-span-6 flex flex-col gap-4 h-[500px] md:h-auto">
                        <div className="flex-1 rounded-[2.5rem] border border-white/5 bg-[#0a0a0c]/80 backdrop-blur-xl relative overflow-hidden shadow-2xl flex flex-col group/chart">
                            <div className="flex-1 w-full h-full">
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
                    </div>

                    {/* COL 3: EXECUTION (Bottom on mobile, Right on desktop) */}
                    <div className="order-3 md:order-3 md:col-span-3 flex flex-col gap-4">
                        <div className="flex items-center justify-between px-1">
                            <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.2em]">Deployment Node</h3>
                        </div>
                        <div className="flex-1 rounded-[2rem] border border-white/5 bg-gradient-to-b from-[#0a0a0c]/80 to-[#050505]/80 backdrop-blur-md overflow-hidden shadow-xl border-t-white/10">
                            <PaperBotWidget />
                        </div>
                    </div>

                </div>
            </main>
        </div>
    );
}

