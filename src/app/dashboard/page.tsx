'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import Pusher from 'pusher-js';
import SignalCard from '@/components/SignalCard';
import SystemLogs from '@/components/SystemLogs';
import { Zap, Activity, LogOut, User, TrendingUp, Lock, Globe } from 'lucide-react';
import PaperBotWidget from '@/components/PaperBotWidget';
import OracleMonitor from '@/components/OracleMonitor';
import PortfolioHub from '@/components/PortfolioHub';
import AIChatModal from '@/components/AIChatModal'; // V1600
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import PerformanceStats from '@/components/PerformanceStats'; // V1500
import SubscriptionGuard from '@/components/SubscriptionGuard'; // V1800
import { useProfile } from '@/hooks/useProfile'; // V1800

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
    atr_value?: number;
    volume_ratio?: number;
    analytics_signals?: {
        imbalance_ratio: number;
        depth_score: number;
        spread_pct: number;
    }[];
}

export default function Dashboard() {
    const [signals, setSignals] = useState<Signal[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null);
    const [activeChatSignal, setActiveChatSignal] = useState<Signal | null>(null); // V1600
    const [customSymbol, setCustomSymbol] = useState<string | null>(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true); // Default open on desktop
    const [mounted, setMounted] = useState(false);
    const [user, setUser] = useState<any>(null);
    const [currentView, setCurrentView] = useState<'dashboard' | 'bot' | 'logs'>('dashboard');
    const router = useRouter();
    const { profile, isVip } = useProfile(); // V1800

    const handleViewChart = (symbol: string) => {
        const sig = signals.find(s => s.symbol === symbol);
        if (sig) {
            setSelectedSignal(sig);
            setCustomSymbol(null);
        } else {
            setSelectedSignal(null);
            setCustomSymbol(symbol);
        }

        if (window.innerWidth < 1024) {
            const chartElement = document.getElementById('main-chart-area');
            chartElement?.scrollIntoView({ behavior: 'smooth' });
        }
    };

    // V1600: Open AI Chat
    const handleConsultAI = (signal: any) => {
        setActiveChatSignal(signal);
    };

    const fetchSignals = async () => {
        try {
            // 1. Try fetching with VIP Join (Preferred)
            const { data, error } = await supabase
                .from('signals')
                .select('*, vip_signal_details(*)')
                .order('created_at', { ascending: false })
                .limit(100);

            if (error) throw error; // If this fails (e.g. missing table), go to catch

            if (data) {
                const formatted = data.map((s: any) => {
                    const vipDetails = Array.isArray(s.vip_signal_details) ? s.vip_signal_details[0] : s.vip_signal_details;
                    return {
                        id: s.id,
                        symbol: s.symbol,
                        // Priority: VIP Table -> Public Table -> 0
                        price: Number(vipDetails?.entry_price || s.entry_price || 0),
                        stop_loss: Number(vipDetails?.sl_price || s.sl_price || 0),
                        take_profit: Number(vipDetails?.tp_price || s.tp_price || 0),
                        rsi: Number(s.rsi || 50),
                        signal_type: s.direction === 'LONG' ? 'BUY' : 'SELL',
                        confidence: Number(s.ai_confidence),
                        timestamp: s.created_at,
                        atr_value: Number(s.atr_value || 0),
                        volume_ratio: Number(s.volume_ratio || 0)
                    };
                });
                setSignals(getUniqueSignals(formatted));
                if (formatted.length > 0 && !selectedSignal) {
                    const unique = getUniqueSignals(formatted);
                    if (unique.length > 0) setSelectedSignal(unique[0]);
                }
            }
        } catch (err) {
            console.warn("VIP Join failed, falling back to public signals:", err);
            // 2. Fallback: Fetch Public Signals Only
            const { data: publicData } = await supabase
                .from('signals')
                .select('*')
                .order('created_at', { ascending: false })
                .limit(100);

            if (publicData) {
                const formatted = publicData.map((s: any) => ({
                    id: s.id,
                    symbol: s.pair,
                    price: Number(s.entry_price || 0),
                    stop_loss: Number(s.sl_price || 0),
                    take_profit: Number(s.tp_price || 0),
                    rsi: Number(s.rsi || 50),
                    signal_type: s.direction === 'LONG' ? 'BUY' : 'SELL',
                    confidence: Number(s.ai_confidence),
                    timestamp: s.created_at,
                    atr_value: Number(s.atr_value || 0),
                    volume_ratio: Number(s.volume_ratio || 0)
                }));
                setSignals(getUniqueSignals(formatted));
                const unique = getUniqueSignals(formatted);
                if (unique.length > 0) setSelectedSignal(unique[0]);
            }
        }
        setLoading(false);
    };

    // V1500: Smart Deduplication
    const getUniqueSignals = (rawSignals: Signal[]) => {
        const seen = new Set();
        return rawSignals.filter(signal => {
            if (seen.has(signal.symbol)) return false;
            seen.add(signal.symbol);
            return true;
        });
    };

    const uniqueSignals = getUniqueSignals(signals);

    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'unavailable'>('connecting');

    useEffect(() => {
        setMounted(true);

        const checkAuth = async () => {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) {
                router.push('/login');
                return;
            }
            setUser(session.user);
            fetchSignals(); // Initial Static Load
        };

        checkAuth();

        if (window.innerWidth < 1280) setIsSidebarOpen(false);

        // V2100: PUSHER REALTIME (Low Latency)
        // Re-connect whenever 'isVip' changes to ensure we subscribe to the right channels
        const pusher = new Pusher(process.env.NEXT_PUBLIC_PUSHER_KEY!, {
            cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
            authEndpoint: '/api/pusher/auth',
            forceTLS: true,
        });

        pusher.connection.bind('connected', () => {
            setConnectionStatus('connected');
            console.log('[Pusher] Connected to ' + process.env.NEXT_PUBLIC_PUSHER_CLUSTER);
        });
        pusher.connection.bind('unavailable', () => setConnectionStatus('unavailable'));
        pusher.connection.bind('failed', () => setConnectionStatus('unavailable'));

        // 1. Public Channel (Always)
        const publicChannel = pusher.subscribe('public-signals');
        publicChannel.bind('new-signal', (data: any) => {
            console.log('Pusher Public Event:', data);
            handleNewSignal(data);
        });

        // 2. VIP Channel (Conditional)
        if (isVip) {
            console.log("Subscribing to VIP Channel...");
            const privateChannel = pusher.subscribe('private-vip-signals');
            privateChannel.bind('pusher:subscription_succeeded', () => {
                console.log('[Pusher] Canal Privado conectado exitosamente');
            });
            privateChannel.bind('new-signal', (data: any) => {
                console.log('Pusher VIP Event:', data);
                handleNewSignal(data);
            });
            privateChannel.bind('pusher:subscription_error', (status: any) => {
                console.error("VIP Auth Failed:", status);
                // Could act here to force logout or show error
            });
        }

        const handleNewSignal = (s: any) => {
            const newSignal: Signal = {
                id: s.id,
                symbol: s.symbol,
                price: Number(s.price || s.entry_price || 0),
                rsi: Number(s.rsi || 50),
                signal_type: s.signal_type,
                confidence: Number(s.confidence),
                timestamp: s.created_at || new Date().toISOString(),
                stop_loss: Number(s.stop_loss || s.sl_price || 0),
                take_profit: Number(s.take_profit || s.tp_price || 0),
                atr_value: Number(s.atr_value || 0),
                volume_ratio: Number(s.volume_ratio || 0)
            };

            setSignals((prev) => {
                const exists = prev.find(sig => sig.id === newSignal.id);
                if (exists) {
                    return prev.map(sig => {
                        if (sig.id === newSignal.id) {
                            return {
                                ...sig,
                                ...newSignal,
                                price: newSignal.price || sig.price,
                                stop_loss: newSignal.stop_loss || sig.stop_loss,
                                take_profit: newSignal.take_profit || sig.take_profit
                            };
                        }
                        return sig;
                    });
                }
                return [newSignal, ...prev].slice(0, 100);
            });
        };

        return () => {
            pusher.unsubscribe('public-signals');
            if (isVip) pusher.unsubscribe('private-vip-signals');
            pusher.disconnect();
        };
    }, [isVip]); // Re-run when VIP status updates dynamically

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
                        <div className="w-10 h-10 rounded-xl overflow-hidden bg-black flex items-center justify-center shadow-[0_0_30px_rgba(0,255,163,0.3)] border border-[#00ffa3]/20 relative">
                            <img
                                src="/logo.png"
                                alt="Nexus Logo"
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                    e.currentTarget.style.display = 'none';
                                    e.currentTarget.parentElement?.classList.add('bg-gradient-to-br', 'from-[#00ffa3]', 'to-[#00ce82]');
                                    const fallback = document.createElement('div');
                                    fallback.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-zap text-black"><path d="M4 14.71 14.5 4H15l-1.5 5.29H20l-10.5 10.71H9l1.5-5.29H4z"/></svg>';
                                    e.currentTarget.parentElement?.appendChild(fallback.firstChild as Node);
                                }}
                            />
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
                    <div className={`hidden lg:flex items-center gap-3 px-4 py-2 rounded-2xl border ${connectionStatus === 'connected' ? 'bg-white/[0.03] border-white/5 text-[#00ffa3]' : 'bg-red-500/10 border-red-500/20 text-red-500'}`}>
                        <span className={`w-2 h-2 rounded-full bg-current shadow-[0_0_10px_currentColor] ${connectionStatus === 'connected' ? 'animate-pulse' : ''}`}></span>
                        <span className="text-[10px] font-black tracking-widest uppercase">
                            {connectionStatus === 'connected' ? 'LIVE DATA STREAM' : 'CONNECTION LOST'}
                        </span>
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

                        <button
                            onClick={() => setCurrentView('dashboard')}
                            className={`w-full flex items-center justify-between px-5 py-4 rounded-2xl border transition-all duration-300 group
                                ${currentView === 'dashboard'
                                    ? 'bg-gradient-to-r from-[#00ffa3]/10 to-transparent text-[#00ffa3] border-[#00ffa3]/20 shadow-[0_0_20px_-5px_rgba(0,255,163,0.2)]'
                                    : 'text-gray-500 hover:text-white hover:bg-white/[0.03] border-transparent hover:border-white/5'
                                }
                            `}
                        >
                            <div className="flex items-center gap-4">
                                <Activity size={18} className={currentView === 'dashboard' ? "animate-pulse" : ""} />
                                <span className="text-sm font-black tracking-tight">AI TERMINAL</span>
                            </div>
                            {currentView === 'dashboard' && <Zap size={14} fill="currentColor" />}
                        </button>

                        <button
                            onClick={() => router.push('/dashboard/market')}
                            className="w-full flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-300 border text-gray-500 hover:text-white hover:bg-white/[0.03] border-transparent hover:border-white/5"
                        >
                            <Globe size={18} />
                            <span className="text-sm font-bold tracking-tight">MARKET OVERVIEW</span>
                        </button>

                        <button
                            onClick={() => router.push('/dashboard/exchange')}
                            className="w-full flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-300 border text-gray-500 hover:text-white hover:bg-white/[0.03] border-transparent hover:border-white/5"
                        >
                            <Activity size={18} />
                            <span className="text-sm font-bold tracking-tight">LIVE EXCHANGE</span>
                        </button>

                        <button
                            onClick={() => setCurrentView('bot')}
                            className={`w-full flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-300 border
                                ${currentView === 'bot'
                                    ? 'bg-white/[0.05] text-white border-white/10'
                                    : 'text-gray-500 hover:text-white hover:bg-white/[0.03] border-transparent hover:border-white/5'
                                }
                            `}
                        >
                            <Zap size={18} />
                            <span className="text-sm font-bold tracking-tight">PAPER BOT ENGINE</span>
                        </button>

                        <button
                            onClick={() => setCurrentView('logs')}
                            className={`w-full flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-300 border
                                ${currentView === 'logs'
                                    ? 'bg-white/[0.05] text-white border-white/10'
                                    : 'text-gray-500 hover:text-white hover:bg-white/[0.03] border-transparent hover:border-white/5'
                                }
                            `}
                        >
                            <Activity size={18} />
                            <span className="text-sm font-bold tracking-tight">ALGORITHMIC LOGS</span>
                        </button>

                        <button
                            onClick={() => window.open('/live', '_blank')}
                            className={`w-full flex items-center gap-4 px-5 py-4 rounded-2xl transition-all duration-300 border text-[#00ffa3]/50 hover:text-[#00ffa3] hover:bg-[#00ffa3]/5 border-transparent hover:border-[#00ffa3]/10`}
                        >
                            <TrendingUp size={18} />
                            <span className="text-sm font-bold tracking-tight">LIVE ENGINE WEBLINK</span>
                        </button>
                    </nav>

                    <div className="p-6 space-y-4">
                        <div className="p-5 rounded-3xl bg-white/[0.03] border border-white/5 relative overflow-hidden group">
                            <div className="absolute top-0 right-0 w-24 h-24 bg-[#00ffa3]/5 rounded-full blur-3xl -mr-12 -mt-12 transition-all group-hover:bg-[#00ffa3]/10"></div>
                            <div className="flex items-center gap-3 mb-2">
                                <div className="w-5 h-5 rounded-lg overflow-hidden flex items-center justify-center bg-black border border-white/10 relative">
                                    <img
                                        src="/logo.png"
                                        alt="Node"
                                        className="w-full h-full object-cover"
                                        onError={(e) => {
                                            e.currentTarget.style.display = 'none';
                                            e.currentTarget.parentElement?.classList.add('bg-[#00ffa3]');
                                            const dot = document.createElement('div');
                                            dot.className = 'w-1.5 h-1.5 bg-black rounded-full';
                                            e.currentTarget.parentElement?.appendChild(dot);
                                        }}
                                    />
                                </div>
                                <p className="text-[10px] text-gray-500 uppercase tracking-widest font-black flex items-center gap-2">
                                    <span className="w-1.5 h-1.5 rounded-full bg-[#00ffa3] animate-ping"></span>
                                    Node Status
                                </p>
                            </div>
                            <div className="flex items-end justify-between">
                                <div>
                                    <span className="text-sm font-black text-white block">{user?.email?.split('@')[0].toUpperCase() || 'ANONYMOUS'}</span>
                                    <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${isVip ? 'bg-[#00ffa3] text-black' : 'bg-gray-700 text-gray-300'}`}>
                                        {isVip ? 'VIP PLAN' : 'FREE PLAN'}
                                    </span>
                                </div>
                                <span className="text-[9px] font-mono text-gray-600 uppercase">99.9% Uptime</span>
                            </div>
                        </div>

                        <button
                            onClick={async () => {
                                await supabase.auth.signOut();
                                router.push('/login');
                            }}
                            className="w-full flex items-center gap-4 px-5 py-4 text-red-500/50 hover:text-red-500 hover:bg-red-500/5 rounded-2xl transition-all duration-300 border border-transparent hover:border-red-500/10 group"
                        >
                            <LogOut size={18} className="group-hover:rotate-12 transition-transform" />
                            <span className="text-sm font-black tracking-tight">LOGOUT SYSTEM</span>
                        </button>
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
                <main className="flex-1 flex flex-col relative overflow-hidden bg-black">

                    {/* Background Pattern - subtle grid */}
                    <div className="absolute inset-0 opacity-[0.05] pointer-events-none"
                        style={{
                            backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px)',
                            backgroundSize: '30px 30px'
                        }}>
                    </div>

                    {/* Ambient Glow */}
                    <div className="absolute top-[-20%] right-[-10%] w-[500px] h-[500px] bg-[#00ffa3]/5 rounded-full blur-[120px] pointer-events-none"></div>

                    {currentView === 'dashboard' && (
                        <div className="flex-1 p-4 lg:p-8 grid grid-cols-1 xl:grid-cols-12 gap-8 overflow-y-auto lg:overflow-hidden z-20 custom-scrollbar animate-fade-in">

                            {/* V1500: PERFORMANCE DASHBOARD (Full Width) - PROTECTED */}
                            <div className="xl:col-span-12">
                                <SubscriptionGuard fallback={
                                    <div className="w-full h-[100px] bg-[#0e0e10] border border-white/5 rounded-3xl flex items-center justify-between px-8">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 rounded-full bg-white/5 flex items-center justify-center">
                                                <Lock className="text-gray-500" size={18} />
                                            </div>
                                            <div>
                                                <h3 className="text-white font-bold">Performance Analytics</h3>
                                                <p className="text-gray-500 text-xs">Unlock your win-rate and profit stats.</p>
                                            </div>
                                        </div>
                                        <button className="px-6 py-2 bg-[#00ffa3] text-black font-black text-xs uppercase tracking-widest rounded-full">
                                            UNLOCK VIP
                                        </button>
                                    </div>
                                }>
                                    <PerformanceStats />
                                </SubscriptionGuard>
                            </div>

                            {/* COL 1: ADVANCED SIGNALS (3 Columns) */}
                            <div className="xl:col-span-3 flex flex-col gap-6 overflow-hidden min-h-[400px] lg:min-h-0 bg-white/[0.02] backdrop-blur-xl rounded-[2.5rem] border border-white/5 p-6 shadow-2xl relative group">
                                <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none group-hover:bg-white/[0.04] transition-colors duration-500"></div>
                                <div className="flex items-center justify-between px-2 relative z-10">
                                    <h3 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.4em]">Signal Pulse</h3>
                                    <div className="flex items-center gap-2 bg-[#00ffa3]/10 px-3 py-1 rounded-full border border-[#00ffa3]/20 shadow-[0_0_10px_rgba(0,255,163,0.1)]">
                                        <span className="text-[10px] text-[#00ffa3] font-black font-mono">{signals.length} ANALYZED</span>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto space-y-4 pr-3 custom-scrollbar-wide pb-4 relative z-10">
                                    {loading ? (
                                        <div className="space-y-4">
                                            {[1, 2, 3, 4].map(i => <div key={i} className="h-32 rounded-3xl bg-white/5 animate-pulse border border-white/5"></div>)}
                                        </div>
                                    ) : (
                                        <>
                                            {/* V1300: HOT SIGNALS (80%+ Confidence - VIP Zone) */}
                                            {uniqueSignals.filter(s => s.confidence >= 80).length > 0 && (
                                                <div className="mb-4 space-y-3">
                                                    <div className="flex items-center gap-2 px-1">
                                                        <div className="text-orange-500 animate-fire">
                                                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                                                                <path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a5.5 5.5 0 1 1-11 0c0-.536.22-1.072.5-1.5Z" />
                                                            </svg>
                                                        </div>
                                                        <span className="text-[10px] font-black text-orange-500 uppercase tracking-widest animate-pulse">HOT ZONE - ELITE SIGNALS</span>
                                                    </div>

                                                    {uniqueSignals.filter(s => s.confidence >= 80).map((signal) => (
                                                        <div key={signal.id} className="relative group/hot">
                                                            <div className="absolute -inset-1 bg-gradient-to-r from-orange-600 to-red-600 rounded-3xl blur opacity-20 group-hover/hot:opacity-50 transition duration-500 animate-fire"></div>
                                                            <SignalCard
                                                                {...signal}
                                                                imbalance={signal.analytics_signals?.[0]?.imbalance_ratio}
                                                                depth_score={signal.analytics_signals?.[0]?.depth_score}
                                                                onViewChart={handleViewChart}
                                                                onConsultAI={handleConsultAI}
                                                                compact={true}
                                                            />
                                                        </div>
                                                    ))}

                                                    <div className="h-px bg-gradient-to-r from-transparent via-white/10 to-transparent my-4"></div>
                                                </div>
                                            )}

                                            {/* REGULAR SIGNALS (<80% Confidence) */}
                                            {uniqueSignals.filter(s => s.confidence < 80).map((signal) => (
                                                <SignalCard
                                                    key={signal.id}
                                                    {...signal}
                                                    imbalance={signal.analytics_signals?.[0]?.imbalance_ratio}
                                                    depth_score={signal.analytics_signals?.[0]?.depth_score}
                                                    onViewChart={handleViewChart}
                                                    onConsultAI={handleConsultAI}
                                                    compact={true}
                                                />
                                            ))}
                                        </>
                                    )}
                                </div>
                            </div>

                            {/* COL 2: MAIN CHART ENGINE (6 Columns) */}
                            <div id="main-chart-area" className="xl:col-span-6 flex flex-col">
                                <div className="flex-1 min-h-[500px] rounded-[2rem] border border-white/10 bg-[#0a0a0c]/80 backdrop-blur-3xl relative overflow-hidden shadow-[0_0_50px_rgba(0,0,0,0.5)] flex flex-col group/chart transition-all hover:border-white/20">
                                    <div className="flex-1 w-full h-full relative">
                                        <div className="absolute inset-0 bg-gradient-to-b from-[#00ffa3]/5 to-transparent pointer-events-none"></div>
                                        <SmartChart
                                            symbol={selectedSignal?.symbol || customSymbol || 'BTC/USD'}
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

                            {/* COL 3: OPERATIONS & ORACLE (3 Columns) */}
                            <div className="xl:col-span-3 flex flex-col gap-6 overflow-hidden min-h-[400px] lg:min-h-0">
                                {/* V90: Portfolio Hub - AI Multi-Asset Leaderboard */}
                                <PortfolioHub />

                                {/* Oracle Insights - High Priority Realtime Feed */}
                                <OracleMonitor />

                                {/* Positions & Wallet */}
                                <div className="flex-1 flex flex-col rounded-[2.5rem] border border-white/10 bg-[#0a0a0c]/80 backdrop-blur-2xl shadow-2xl relative overflow-hidden group hover:border-[#00ffa3]/30 transition-all duration-500">
                                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#00ffa3]/40 to-transparent"></div>
                                    <div className="flex-1">
                                        <PaperBotWidget onSelectSymbol={handleViewChart} />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {currentView === 'bot' && (
                        <div className="flex-1 p-6 overflow-hidden z-20 animate-slide-up">
                            <div className="h-full rounded-[2.5rem] border border-white/10 bg-[#0a0a0c]/60 backdrop-blur-2xl shadow-2xl overflow-hidden relative flex flex-col">
                                <div className="p-6 border-b border-white/5 flex items-center gap-4 bg-white/[0.02]">
                                    <Zap size={24} className="text-[#00ffa3]" />
                                    <h1 className="text-2xl font-black tracking-tighter text-white">AUTONOMOUS PAPER ENGINE</h1>
                                </div>
                                <div className="flex-1 relative">
                                    <div className="absolute inset-0">
                                        <PaperBotWidget onSelectSymbol={handleViewChart} viewMode="pro" />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {currentView === 'logs' && (
                        <div className="flex-1 p-6 overflow-hidden z-20 flex flex-col animate-slide-up">
                            <div className="h-full rounded-[2.5rem] border border-white/10 bg-[#0a0a0c]/80 backdrop-blur-md shadow-2xl overflow-hidden relative">
                                <SystemLogs onClose={() => setCurrentView('dashboard')} />
                            </div>
                        </div>
                    )}
                </main>
            </div>
            {/* V1600: AI Modal */}
            {activeChatSignal && (
                <AIChatModal
                    signal={activeChatSignal}
                    isOpen={!!activeChatSignal}
                    onClose={() => setActiveChatSignal(null)}
                />
            )}
        </div>
    );
}
