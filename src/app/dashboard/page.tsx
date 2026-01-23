'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import SignalCard from '@/components/SignalCard';
import { Zap } from 'lucide-react';
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

    const handleViewChart = (symbol: string) => {
        const sig = signals.find(s => s.symbol === symbol);
        if (sig) {
            setSelectedSignal(sig);
        }
    };

    // ... (fetchSignals and useEffect remain same)

    // Fetch initial data
    const fetchSignals = async () => {
        const { data, error } = await supabase
            .from('market_signals')
            .select('*')
            .order('timestamp', { ascending: false })
            .limit(50); // Increased limit for feed

        if (error) console.error('Error fetching signals:', error);
        else {
            setSignals(data || []);
            // Auto-select first signal if none selected
            if (data && data.length > 0 && !selectedSignal) {
                setSelectedSignal(data[0]);
            }
        }
        setLoading(false);
    };

    // Prevent Hydration Mismatch by running only on client
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        fetchSignals();

        // Real-time Subscription
        const channel = supabase
            .channel('realtime signals')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'market_signals' }, (payload: any) => {
                const newSignal = payload.new as Signal;
                setSignals((prev) => [newSignal, ...prev].slice(0, 100));
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    if (!mounted) return <div className="h-screen bg-[#050505] flex items-center justify-center text-gray-800 font-mono">Initializing Nexus Terminal...</div>;

    return (
        <div className="h-screen bg-[#050505] text-white font-sans overflow-hidden flex">
            {/* SIDEBAR NAVIGATION */}
            <aside className="w-64 border-r border-white/5 bg-[#0a0a0c] flex flex-col z-50">
                {/* Logo Area */}
                <div className="h-16 flex items-center px-6 border-b border-white/5">
                    <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#00ffa3] to-[#00ce82] flex items-center justify-center text-black shadow-[0_0_20px_rgba(0,255,163,0.3)]">
                            <Zap size={18} fill="currentColor" />
                        </div>
                        <span className="font-bold tracking-wide text-lg">NEXUS<span className="text-[#00ffa3]">AI</span></span>
                    </div>
                </div>

                {/* Nav Links */}
                <nav className="flex-1 p-4 space-y-1">
                    <div className="px-3 py-2 text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Platform</div>
                    <button className="w-full flex items-center gap-3 px-3 py-2.5 bg-white/5 text-white rounded-lg border border-white/5">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#00ffa3] shadow-[0_0_10px_#00ffa3]"></div>
                        <span className="text-sm font-medium">Terminal</span>
                    </button>
                    <button className="w-full flex items-center gap-3 px-3 py-2.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                        <div className="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                        <span className="text-sm font-medium">Paper Bot</span>
                    </button>
                    <button className="w-full flex items-center gap-3 px-3 py-2.5 text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors">
                        <div className="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                        <span className="text-sm font-medium">Settings</span>
                    </button>
                </nav>

                {/* System Status */}
                <div className="p-4 border-t border-white/5">
                    <div className="p-3 rounded-xl bg-white/5 border border-white/5">
                        <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">System Status</p>
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 rounded-full bg-[#00ffa3] animate-pulse"></div>
                            <span className="text-xs font-bold text-[#00ffa3]">OPERATIONAL</span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* MAIN CONTENT AREA */}
            <main className="flex-1 flex flex-col relative overflow-hidden bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-[#1a1a2e] via-[#050505] to-[#050505]">

                {/* Top Bar */}
                <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[#0a0a0c]/50 backdrop-blur-md">
                    <div className="flex items-center gap-4">
                        <div className="h-8 w-px bg-white/10"></div>
                        <h2 className="text-sm font-medium text-gray-400">Market Overview</h2>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#00ffa3]/10 border border-[#00ffa3]/20 text-[#00ffa3]">
                            <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
                            <span className="text-xs font-bold tracking-wide">LIVE FEED</span>
                        </div>
                    </div>
                </header>

                {/* Dashboard Grid */}
                <div className="flex-1 overflow-hidden p-6 grid grid-cols-12 gap-6">

                    {/* LEFT COLUMN: SIGNALS */}
                    <div className="col-span-3 flex flex-col gap-4 overflow-hidden">
                        <div className="flex items-center justify-between">
                            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest">Signal Feed</h3>
                            <span className="text-xs text-gray-600 font-mono">{signals.length} Active</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                            {loading ? (
                                <div className="space-y-3">
                                    {[1, 2, 3].map(i => <div key={i} className="h-24 rounded-lg bg-white/5 animate-pulse"></div>)}
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

                    {/* CENTER COLUMN: CHART */}
                    <div className="col-span-6 flex flex-col gap-4">
                        {selectedSignal ? (
                            <div className="flex-1 rounded-3xl border border-white/5 bg-[#0a0a0c]/80 backdrop-blur-xl relative overflow-hidden shadow-2xl flex flex-col">
                                {/* Chart Header overlay */}
                                <div className="absolute top-0 left-0 w-full p-6 z-10 flex justify-between items-start bg-gradient-to-b from-black/80 to-transparent pointer-events-none">
                                    <div>
                                        <h1 className="text-3xl font-bold font-sans tracking-tight flex items-center gap-3">
                                            {selectedSignal.symbol}
                                            <span className="text-2xl text-gray-500 font-normal tracking-normal">
                                                ${selectedSignal.price.toLocaleString()}
                                            </span>
                                        </h1>
                                        <div className="flex items-center gap-2 mt-2">
                                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-white/10 text-gray-300 border border-white/5">1H Interval</span>
                                            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#00ffa3]/10 text-[#00ffa3] border border-[#00ffa3]/20">AI Confidence: {selectedSignal.confidence}%</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Chart Container */}
                                <div className="flex-1 w-full h-full pt-16">
                                    <SmartChart
                                        symbol={selectedSignal.symbol}
                                        signalData={{
                                            entry: selectedSignal.price,
                                            stop_loss: selectedSignal.stop_loss,
                                            take_profit: selectedSignal.take_profit,
                                            confidence: selectedSignal.confidence,
                                            signal_type: selectedSignal.signal_type
                                        }}
                                    />
                                </div>
                            </div>
                        ) : (
                            <div className="flex-1 rounded-3xl border border-white/5 bg-[#0a0a0c]/50 flex items-center justify-center">
                                <div className="text-center">
                                    <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mx-auto mb-4">
                                        <Zap className="text-gray-600" />
                                    </div>
                                    <p className="text-gray-500 font-mono">Select a signal to initialize chart</p>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* RIGHT COLUMN: EXECUTION */}
                    <div className="col-span-3 flex flex-col gap-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest">Active Bot</h3>
                        </div>
                        <div className="flex-1 rounded-2xl border border-white/5 bg-[#0a0a0c]/60 backdrop-blur-md overflow-hidden">
                            <PaperBotWidget />
                        </div>
                    </div>

                </div>
            </main>
        </div>
    );
}
