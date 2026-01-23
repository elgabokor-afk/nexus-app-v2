'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import SignalCard from '@/components/SignalCard';
import { Zap } from 'lucide-react';
import { SmartChart } from '@/components/SmartChart';
import PaperBotWidget from '@/components/PaperBotWidget';

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

    useEffect(() => {
        fetchSignals();

        // Real-time Subscription
        const channel = supabase
            .channel('realtime signals')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'market_signals' }, (payload) => {
                const newSignal = payload.new as Signal;
                setSignals((prev) => [newSignal, ...prev].slice(0, 100));
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    return (
        <div className="h-screen bg-[#050505] text-white font-sans overflow-hidden flex flex-col">
            {/* COMPACT HEADER */}
            <header className="h-14 bg-[#000] border-b border-[#222] flex items-center justify-between px-4 shrink-0 z-50">
                <div className="flex items-center gap-2">
                    <Zap className="text-[#00ffa3] fill-current" size={18} />
                    <span className="font-mono font-bold tracking-wider">
                        TRENDS<span className="text-[#00ffa3]">AI</span> TERMINAL
                    </span>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2 px-2 py-1 bg-[#111] rounded border border-[#333]">
                        <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-[10px] text-gray-400 font-mono">LIVE</span>
                    </div>
                </div>
            </header>

            {/* MAIN TERMINAL GRID */}
            <main className="flex-1 grid grid-cols-12 overflow-hidden">
                {/* COL 1: SIGNAL FEED (LEFT) */}
                <div className="col-span-3 border-r border-[#222] flex flex-col bg-[#080808]">
                    <div className="p-3 border-b border-[#222] bg-[#0a0a0c]">
                        <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Signal Feed</h2>
                    </div>
                    <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
                        {loading ? (
                            <div className="text-center py-10 text-xs text-gray-500 font-mono">Connecting to Node...</div>
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

                {/* COL 2: CENTER STAGE (CHART) */}
                <div className="col-span-6 bg-black flex flex-col relative border-r border-[#222]">
                    {selectedSignal ? (
                        <>
                            <div className="absolute top-4 left-4 z-10">
                                <h1 className="text-2xl font-bold font-mono tracking-tighter flex items-center gap-2">
                                    {selectedSignal.symbol}
                                    <span className="text-lg text-gray-500 font-normal">
                                        ${selectedSignal.price.toLocaleString()}
                                    </span>
                                </h1>
                            </div>
                            <div className="flex-1 w-full h-full">
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
                        </>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-gray-600 font-mono">
                            SELECT SIGNAL TO INITIALIZE FEED
                        </div>
                    )}
                </div>

                {/* COL 3: EXECUTION / PAPER BOT (RIGHT) */}
                <div className="col-span-3 bg-[#0a0a0c] flex flex-col overflow-y-auto border-l border-[#222]">
                    <div className="p-3 border-b border-[#222] bg-[#0a0a0c]">
                        <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Algo Execution</h2>
                    </div>
                    <div className="p-4">
                        <PaperBotWidget />
                    </div>

                    {/* Additional Stats Placeholder */}
                    <div className="p-4 border-t border-[#222] mt-auto">
                        <div className="bg-[#111] rounded p-3 text-center">
                            <p className="text-[10px] text-gray-500 mb-1">SYSTEM STATUS</p>
                            <p className="text-xs text-[#00ffa3] font-mono">OPTIMAL</p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
