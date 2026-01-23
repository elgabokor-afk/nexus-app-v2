'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import SignalCard from '@/components/SignalCard';
import { Zap } from 'lucide-react';

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



export default function Dashboard() {
    const [signals, setSignals] = useState<Signal[]>([]);
    const [loading, setLoading] = useState(true);

    // Fetch initial data
    const fetchSignals = async () => {
        const { data, error } = await supabase
            .from('market_signals')
            .select('*')
            .order('timestamp', { ascending: false })
            .limit(20);

        if (error) console.error('Error fetching signals:', error);
        else setSignals(data || []);
        setLoading(false);
    };

    useEffect(() => {
        fetchSignals();

        // Real-time Subscription
        const channel = supabase
            .channel('realtime signals')
            .on('postgres_changes', { event: 'INSERT', schema: 'public', table: 'market_signals' }, (payload) => {
                const newSignal = payload.new as Signal;
                setSignals((prev) => [newSignal, ...prev].slice(0, 50)); // Keep last 50
            })
            .subscribe();

        return () => {
            supabase.removeChannel(channel);
        };
    }, []);

    useEffect(() => {
        // Load TradingView Script
        const script = document.createElement('script');
        script.src = 'https://s3.tradingview.com/tv.js';
        script.async = true;
        script.onload = () => {
            // @ts-ignore
            if (window.TradingView) {
                new window.TradingView.widget({
                    "autosize": true,
                    "symbol": "KRAKEN:XBTUSD",
                    "interval": "60",
                    "timezone": "Etc/UTC",
                    "theme": "dark",
                    "style": "1",
                    "locale": "en",
                    "enable_publishing": false,
                    "backgroundColor": "rgba(5, 5, 5, 1)",
                    "gridColor": "rgba(40, 40, 40, 1)",
                    "hide_top_toolbar": false,
                    "hide_legend": false,
                    "save_image": false,
                    "container_id": "tradingview_widget"
                });
            }
        };
        document.head.appendChild(script);

        return () => {
            // Cleanup provided by script remove isn't strict requirement but good practice
            // if (document.head.contains(script)) document.head.removeChild(script);
        };
    }, []);

    return (
        <div className="min-h-screen bg-[#050505] text-white font-sans selection:bg-[#00ffa3] selection:text-black">
            {/* HEADER */}
            <header className="fixed top-0 w-full h-16 bg-[#000]/80 backdrop-blur-md border-b border-[#222] z-50 flex items-center justify-between px-6">
                <div className="flex items-center gap-2">
                    <Zap className="text-[#00ffa3] fill-current" size={20} />
                    <span className="font-mono font-bold text-lg tracking-wider">
                        TRENDS<span className="text-[#00ffa3]">AI</span> v2
                    </span>
                </div>
                <div className="flex items-center gap-4">
                    <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-[#111] rounded-full border border-[#333]">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                        <span className="text-xs text-gray-400 font-mono">SYSTEM ONLINE</span>
                    </div>
                    <a href="/" className="text-sm text-gray-500 hover:text-white transition-colors">Exit</a>
                </div>
            </header>

            {/* MAIN CONTENT */}
            <main className="pt-24 px-4 md:px-8 max-w-7xl mx-auto">
                <div className="flex justify-between items-end mb-8">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">Live Market Scanner</h1>
                        <p className="text-gray-400">Monitoring 50+ High Volume Pairs via Kraken API</p>
                    </div>
                </div>

                {/* MARKET OVERVIEW - TRADINGVIEW WIDGET */}
                <div className="mb-10 h-[500px] border border-[#222] rounded-2xl overflow-hidden shadow-2xl bg-[#0a0a0c]">
                    <div className="tradingview-widget-container" style={{ height: "100%", width: "100%" }}>
                        <div id="tradingview_widget" style={{ height: "calc(100% - 32px)", width: "100%" }}></div>
                        <div className="tradingview-widget-copyright" style={{ fontSize: '10px', padding: '8px', background: '#000', color: '#666', textAlign: 'center' }}>
                            <a href="https://www.tradingview.com/" rel="noopener nofollow" target="_blank">Track all markets on TradingView</a>
                        </div>
                    </div>
                </div>

                {/* SIGNALS GRID */}
                {loading ? (
                    <div className="flex justify-center items-center h-64 text-[#00ffa3] font-mono animate-pulse">
                        INITIALIZING NEURAL NET...
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {signals.map((signal) => (
                            <SignalCard key={signal.id} {...signal} />
                        ))}

                        {signals.length === 0 && (
                            <div className="col-span-full text-center py-20 text-gray-600 border border-dashed border-[#222] rounded-xl font-mono">
                                Searching for institutional patterns...
                            </div>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
}
