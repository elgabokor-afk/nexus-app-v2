'use client';

import RiskModal from '@/components/RiskModal';
import LegalFooter from '@/components/LegalFooter';
import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import Pusher from 'pusher-js';
import SignalCard from '@/components/SignalCard';
// V3100: Lazy Load Heavy Components for Performance
const SystemLogs = dynamic(() => import('@/components/SystemLogs'), { ssr: false });
const PaperBotWidget = dynamic(() => import('@/components/PaperBotWidget'), { ssr: false });
const OracleMonitor = dynamic(() => import('@/components/OracleMonitor'), { ssr: false });
const PortfolioHub = dynamic(() => import('@/components/PortfolioHub'), { ssr: false });
const AIChatModal = dynamic(() => import('@/components/AIChatModal'), { ssr: false });
const PerformanceStats = dynamic(() => import('@/components/PerformanceStats'), { ssr: false });

import { Zap, Activity, LogOut, User, TrendingUp, Lock, Globe, ExternalLink } from 'lucide-react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
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

const SidebarLink = ({ active, onClick, icon, label }: any) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200 group
            ${active
                ? 'bg-[#1d1f23] text-white border border-[#2f3336]'
                : 'text-gray-500 hover:text-white hover:bg-white/[0.03] border border-transparent'
            }
        `}
    >
        <span className={active ? 'text-[#00ffa3]' : 'text-gray-500 group-hover:text-white'}>{icon}</span>
        <span className="text-sm font-medium">{label}</span>
        {active && <div className="ml-auto w-1 h-1 rounded-full bg-[#00ffa3]"></div>}
    </button>
);

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
                        volume_ratio: Number(s.volume_ratio || 0),
                        status: s.status, // ACTIVE or CLOSED
                        pnl: Number(s.result_pnl || 0)
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
                    symbol: s.symbol,
                    price: Number(s.entry_price || 0),
                    stop_loss: Number(s.sl_price || 0),
                    take_profit: Number(s.tp_price || 0),
                    rsi: Number(s.rsi || 50),
                    signal_type: s.direction === 'LONG' ? 'BUY' : 'SELL',
                    confidence: Number(s.ai_confidence),
                    timestamp: s.created_at,
                    atr_value: Number(s.atr_value || 0),
                    volume_ratio: Number(s.volume_ratio || 0),
                    status: s.status,
                    pnl: Number(s.result_pnl || 0)
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
            // V2588: Visual Confirmation for User
            // Assuming we have a toast library or similar, otherwise standard console
            // If checking "ui" complaints, visible feedback is better.
            // Using standard alert or console if no toast imported, but let's assume valid handle.
            handleNewSignal(data);
        });

        // V2700: LIVE AUDITOR LISTENER
        publicChannel.bind('signal-update', (data: any) => {
            console.log('⚡ [AUDITOR] Update Received:', data);

            setSignals(prev => prev.map(s => {
                if (s.id === data.id) {
                    // Update TP/SL and add Flash Flag
                    return {
                        ...s,
                        stop_loss: data.new_sl || s.stop_loss,
                        take_profit: data.new_tp || s.take_profit,
                        audit_alert: data.audit_action // 'TAKE_PROFIT_TIGHTEN', 'RISK_FREE', 'WARNING'
                    };
                }
                return s;
            }));

            // Optional: Show Toast
            if (data.audit_note) {
                // console.log("Toast:", data.audit_note);
                // If we had a toast lib: toast(data.audit_note, { icon: '⚡' });
            }
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
                // V2588: Fix Key Mapping (Backend sends 'sl'/'tp')
                stop_loss: Number(s.stop_loss || s.sl_price || s.sl || 0),
                take_profit: Number(s.take_profit || s.tp_price || s.tp || 0),
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
        <div className="h-screen bg-black text-white font-sans overflow-hidden flex flex-col selection:bg-[#00ffa3] selection:text-black">

            {/* TOP BAR / HEADER */}
            <header className="h-16 border-b border-[#2f3336] flex items-center justify-between px-6 bg-black z-[60] sticky top-0">
                <div className="flex items-center gap-6">
                    {/* Hamburger Toggle */}
                    <button
                        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                        className="p-2 hover:bg-[#1d1f23] rounded-md transition-all active:scale-95 group"
                    >
                        <div className="space-y-1">
                            <div className={`h-0.5 w-4 bg-gray-400 group-hover:bg-white transition-all ${isSidebarOpen ? 'rotate-45 translate-y-1.5' : ''}`}></div>
                            <div className={`h-0.5 w-4 bg-gray-400 group-hover:bg-white transition-all ${isSidebarOpen ? 'opacity-0' : ''}`}></div>
                            <div className={`h-0.5 w-4 bg-gray-400 group-hover:bg-white transition-all ${isSidebarOpen ? '-rotate-45 -translate-y-1.5' : ''}`}></div>
                        </div>
                    </button>

                    <div className="flex items-center gap-3">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src="/logo.png" alt="NEXUS AI" className="h-8 w-8 object-contain" />
                        <div className="hidden md:flex flex-col">
                            <span className="text-lg font-black tracking-tighter text-white leading-none">NEXUS</span>
                            <span className="text-[9px] font-bold text-[#00ffa3] tracking-widest uppercase">AI Architect v3.0</span>
                        </div>
                    </div>

                    <div className="h-6 w-px bg-[#2f3336] mx-2 hidden md:block"></div>


                    {/* Selected Symbol Display */}
                    {selectedSignal && (
                        <div className="hidden md:flex items-center gap-4 animate-in fade-in slide-in-from-left-2 duration-300">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-bold tracking-tight text-[#E7E9EA]">{selectedSignal.symbol}</span>
                                <span className={`text-xs font-mono font-medium ${selectedSignal.signal_type === 'BUY' ? 'text-[#00ffa3]' : 'text-[#ff4d4d]'}`}>
                                    ${selectedSignal.price.toLocaleString()}
                                </span>
                            </div>

                            <div className="flex items-center gap-2 pl-4 border-l border-[#2f3336]">
                                <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider">AI Score</span>
                                <span className={`text-xs font-bold ${selectedSignal.confidence >= 80 ? 'text-[#00ffa3]' : 'text-gray-300'}`}>{selectedSignal.confidence}%</span>
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-4">
                    <div className={`hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full border ${connectionStatus === 'connected' ? 'bg-[#00ffa3]/10 border-[#00ffa3]/20 text-[#00ffa3]' : 'bg-red-500/10 border-red-500/20 text-red-500'}`}>
                        <span className={`w-1.5 h-1.5 rounded-full bg-current ${connectionStatus === 'connected' ? 'animate-pulse' : ''}`}></span>
                        <span className="text-[10px] font-bold tracking-wide uppercase">
                            {connectionStatus === 'connected' ? 'Live' : 'Offline'}
                        </span>
                    </div>
                </div>
            </header>

            <div className="flex-1 flex overflow-hidden relative">

                {/* SIDEBAR NAVIGATION - Minimalist */}
                <aside className={`
                    fixed md:relative inset-y-0 left-0 w-64 bg-black border-r border-[#2f3336] flex flex-col z-50 transition-all duration-300 ease-out
                    ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full md:-ml-64'}
                `}>
                    <nav className="flex-1 p-4 space-y-1 mt-2">
                        <div className="px-3 py-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2">Platform</div>

                        <SidebarLink
                            active={currentView === 'dashboard'}
                            onClick={() => setCurrentView('dashboard')}
                            icon={<Activity size={18} />}
                            label="Terminal"
                        />
                        <SidebarLink
                            active={false}
                            onClick={() => router.push('/dashboard/market')}
                            icon={<Globe size={18} />}
                            label="Market Overview"
                        />
                        <SidebarLink
                            active={false}
                            onClick={() => router.push('/dashboard/exchange')}
                            icon={<Activity size={18} />}
                            label="Live Exchange"
                        />
                        <SidebarLink
                            active={currentView === 'bot'}
                            onClick={() => setCurrentView('bot')}
                            icon={<Zap size={18} />}
                            label="Paper Engine"
                        />
                        <SidebarLink
                            active={currentView === 'logs'}
                            onClick={() => setCurrentView('logs')}
                            icon={<Activity size={18} />}
                            label="System Logs"
                        />

                        <div className="my-4 border-t border-[#2f3336]"></div>

                        <a href="/live" target="_blank" className="flex items-center gap-3 px-3 py-2.5 rounded-md text-gray-400 hover:text-[#00ffa3] hover:bg-[#00ffa3]/5 transition-colors group">
                            <TrendingUp size={18} />
                            <span className="text-sm font-medium">Live WebLink</span>
                            <ExternalLink size={12} className="opacity-0 group-hover:opacity-100 transition-opacity ml-auto" />
                        </a>
                    </nav>

                    <div className="p-4 border-t border-[#2f3336]">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="w-8 h-8 rounded-lg bg-[#1d1f23] flex items-center justify-center border border-[#2f3336]">
                                <User size={16} className="text-gray-400" />
                            </div>
                            <div className="overflow-hidden">
                                <p className="text-sm font-bold text-white truncate">{user?.email?.split('@')[0]}</p>
                                <p className="text-[10px] text-gray-500 font-medium flex items-center gap-1">
                                    <span className={`w-1.5 h-1.5 rounded-full ${isVip ? 'bg-[#00ffa3]' : 'bg-gray-500'}`}></span>
                                    {isVip ? 'VIP Pro' : 'Free Plan'}
                                </p>
                            </div>
                        </div>

                        <button
                            onClick={async () => {
                                await supabase.auth.signOut();
                                router.push('/login');
                            }}
                            className="w-full flex items-center justify-center gap-2 px-4 py-2 text-xs font-bold text-gray-400 hover:text-white bg-[#1d1f23] hover:bg-[#2f3336] rounded-lg transition-colors border border-[#2f3336]"
                        >
                            <LogOut size={14} />
                            Sign Out
                        </button>
                    </div>

                </aside>

                {/* Backdrop for sidebar */}
                {isSidebarOpen && (
                    <div
                        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 md:hidden animate-in fade-in duration-300"
                        onClick={() => setIsSidebarOpen(false)}
                    />
                )}

                {/* MAIN DASHBOARD CONTENT */}
                <main className="flex-1 flex flex-col relative overflow-hidden bg-black">
                    {/* Clean Background - No Patterns */}

                    {currentView === 'dashboard' && (
                        <div className="flex-1 p-4 lg:p-6 grid grid-cols-1 xl:grid-cols-12 gap-6 overflow-y-auto lg:overflow-hidden z-20 custom-scrollbar animate-fade-in">

                            {/* V1500: PERFORMANCE DASHBOARD (Full Width) - PROTECTED */}
                            <div className="xl:col-span-12">
                                <SubscriptionGuard fallback={
                                    <div className="w-full h-[80px] bg-[#0e0e10] border border-[#2f3336] rounded-xl flex items-center justify-between px-6">
                                        <div className="flex items-center gap-4">
                                            <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center">
                                                <Lock className="text-gray-500" size={16} />
                                            </div>
                                            <div>
                                                <h3 className="text-white font-bold text-sm">Performance Analytics</h3>
                                                <p className="text-gray-500 text-[11px]">Unlock your win-rate and profit stats.</p>
                                            </div>
                                        </div>
                                        <button className="px-5 py-2 bg-[#00ffa3] hover:bg-[#00ffa3]/90 text-black font-bold text-[11px] uppercase tracking-widest rounded-lg transition-colors">
                                            UNLOCK VIP
                                        </button>
                                    </div>
                                }>
                                    <PerformanceStats />
                                </SubscriptionGuard>
                            </div>

                            {/* COL 1: ADVANCED SIGNALS (3 Columns) */}
                            <div className="xl:col-span-3 flex flex-col gap-4 overflow-hidden min-h-[400px] lg:min-h-0 bg-[#0e0e10] rounded-xl border border-[#2f3336] p-0 flex-1">
                                <div className="flex items-center justify-between px-4 py-3 border-b border-[#2f3336]">
                                    <h3 className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">Signal Pulse</h3>
                                    <div className="flex items-center gap-2">
                                        <span className="w-1.5 h-1.5 rounded-full bg-[#00ffa3] animate-pulse"></span>
                                        <span className="text-[10px] text-[#00ffa3] font-mono font-bold">{signals.length} LIVE</span>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto overflow-x-hidden p-3 custom-scrollbar">
                                    {loading ? (
                                        <div className="space-y-3">
                                            {[1, 2, 3, 4].map(i => <div key={i} className="h-24 rounded-lg bg-white/5 animate-pulse"></div>)}
                                        </div>
                                    ) : (
                                        <>
                                            {/* V1300: HOT SIGNALS (80%+ Confidence - VIP Zone) */}
                                            {uniqueSignals.filter(s => s.confidence >= 80).length > 0 && (
                                                <div className="mb-2 space-y-2">
                                                    <div className="flex items-center gap-2 px-1 py-1">
                                                        <span className="text-[9px] font-black text-[#00ffa3] uppercase tracking-widest">ELITE OPPORTUNITIES (80%+)</span>
                                                    </div>

                                                    {uniqueSignals.filter(s => s.confidence >= 80).map((signal) => (
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
                                                    <div className="h-px bg-[#2f3336] my-3"></div>
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
                                <div className="flex-1 min-h-[500px] rounded-xl border border-[#2f3336] bg-[#0e0e10] relative overflow-hidden flex flex-col">
                                    <div className="flex-1 w-full h-full relative">
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
                            <div className="xl:col-span-3 flex flex-col gap-4 overflow-hidden min-h-[400px] lg:min-h-0">
                                {/* V90: Portfolio Hub - AI Multi-Asset Leaderboard */}
                                <PortfolioHub />

                                {/* Oracle Insights - High Priority Realtime Feed */}
                                <OracleMonitor />

                                {/* Positions & Wallet */}
                                <div className="flex-1 flex flex-col rounded-xl border border-[#2f3336] bg-[#0e0e10] relative overflow-hidden">
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
            </div >

            {/* V1600: AI Modal */}
            {
                activeChatSignal && (
                    <AIChatModal
                        signal={activeChatSignal}
                        isOpen={!!activeChatSignal}
                        onClose={() => setActiveChatSignal(null)}
                    />
                )
            }

            {/* V2900: LEGAL COMPLIANCE LAYER */}
            <RiskModal />
        </div >
    );
}
