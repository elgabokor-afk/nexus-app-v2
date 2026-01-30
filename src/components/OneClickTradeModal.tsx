import { useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { Zap, ShieldCheck, AlertTriangle, CheckCircle, Loader2, X } from 'lucide-react';
import ExchangeSettings from './ExchangeSettings';

interface TradeSignal {
    symbol: string;
    side: string;
    entry_price: number;
    stop_loss: number;
    take_profit: number;
}

export default function OneClickTradeModal({
    isOpen,
    onClose,
    signal
}: {
    isOpen: boolean;
    onClose: () => void;
    signal: TradeSignal;
}) {
    const [confirmed, setConfirmed] = useState(false);
    const [status, setStatus] = useState<'IDLE' | 'PROCESSING' | 'SUCCESS' | 'ERROR' | 'CONNECT'>('IDLE');
    const [log, setLog] = useState<string>('');
    const [amount, setAmount] = useState<number>(100);

    // V6001: Automatic Risk Ratio Logic (1:2)
    const calculateRiskParams = () => {
        let tp = signal.take_profit;
        let sl = signal.stop_loss;
        const entry = signal.entry_price;

        if (sl && !tp) {
            // Target = Entry + (Entry - SL) * 2 (for Long)
            const risk = Math.abs(entry - sl);
            tp = signal.side === 'buy' ? entry + risk * 2 : entry - risk * 2;
        } else if (tp && !sl) {
            const reward = Math.abs(tp - entry);
            sl = signal.side === 'buy' ? entry - reward / 2 : entry + reward / 2;
        }
        return { tp, sl };
    };

    const { tp: finalTP, sl: finalSL } = calculateRiskParams();

    const executeTrade = async () => {
        if (!confirmed) return;
        setStatus('PROCESSING');
        setLog('Initializing Secure Execution...');

        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) throw new Error("Authentication Required");

            // 1. Double check keys exist
            const { data: keyCheck } = await supabase.from('user_exchanges').select('id').eq('user_id', user.id).maybeSingle();
            if (!keyCheck) {
                setStatus('CONNECT');
                return;
            }

            setLog('Connecting to Nexus Gateway...');

            setLog('Connecting to Nexus Gateway...');

            // V7000: Use Next.js Proxy to reach internal Railway Service
            const API_URL = "/api/py";

            const res = await fetch(`${API_URL}/execute-trade`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: user.id,
                    symbol: signal.symbol,
                    side: signal.side.toLowerCase(),
                    amount_usd: amount,
                    stop_loss: finalSL,
                    take_profit: finalTP
                })
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Gateway Execution Error");
            }

            setStatus('SUCCESS');
            setLog(`Order Placed Successfully`);

        } catch (e: any) {
            if (e.message.includes('fetch')) {
                setLog("Nexus Gateway UNREACHABLE. Check if Railway service is running.");
            } else {
                setLog(e.message);
            }
            setStatus('ERROR');
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
            <div className="bg-zinc-900 border border-white/10 rounded-3xl w-full max-w-sm overflow-hidden shadow-2xl ring-1 ring-white/5">

                {/* Header */}
                <div className="p-6 border-b border-white/5 flex justify-between items-start">
                    <div>
                        <h2 className="text-xl font-black text-white italic tracking-tighter flex items-center gap-2">
                            <Zap className="text-[#00ffa3] fill-current" />
                            FLASH EXECUTE
                        </h2>
                        <p className="text-xs text-zinc-500 font-mono mt-1">One-Click Production Trade</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full text-zinc-500 hover:text-white transition">
                        <X size={18} />
                    </button>
                </div>

                <div className="p-6 space-y-6">
                    {/* Connect State */}
                    {status === 'CONNECT' && (
                        <div className="animate-in slide-in-from-bottom-4">
                            <div className="bg-yellow-500/10 border border-yellow-500/20 p-4 rounded-xl mb-4 flex items-start gap-3">
                                <AlertTriangle className="text-yellow-500 shrink-0" size={18} />
                                <p className="text-[10px] text-yellow-200 font-bold uppercase tracking-tight">
                                    No exchange connected. Please link your Binance API keys to enable One-Click execution.
                                </p>
                            </div>
                            <div className="scale-90 -mx-4 origin-top">
                                <ExchangeSettings />
                            </div>
                            <button
                                onClick={() => setStatus('IDLE')}
                                className="w-full mt-4 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl text-xs font-bold transition"
                            >
                                Back to Trade
                            </button>
                        </div>
                    )}

                    {status === 'IDLE' && (
                        <>
                            {/* Signal Recap */}
                            <div className="bg-black/40 p-4 rounded-xl border border-white/5 space-y-2">
                                <div className="flex justify-between items-center">
                                    <span className="text-xs font-bold text-zinc-500 uppercase">Pair</span>
                                    <span className="text-sm font-black text-white font-mono">{signal.symbol}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-xs font-bold text-zinc-500 uppercase">Action</span>
                                    <span className={`text-sm font-black uppercase font-mono ${signal.side === 'buy' ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                                        {signal.side}
                                    </span>
                                </div>
                                <div className="flex justify-between items-center pt-2 border-t border-white/5">
                                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Entry</span>
                                    <span className="text-xs font-bold text-white font-mono">{signal.entry_price}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest text-[#00ffa3]">TP (2:1)</span>
                                    <span className="text-xs font-bold text-[#00ffa3] font-mono">{finalTP.toFixed(2)}</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest text-red-500">Stop Loss</span>
                                    <span className="text-xs font-bold text-red-500 font-mono">{finalSL.toFixed(2)}</span>
                                </div>
                            </div>

                            {/* Controls */}
                            <div className="space-y-4">
                                <div>
                                    <label className="text-[10px] font-black uppercase text-zinc-500 tracking-wider mb-2 block">Position Size (USD)</label>
                                    <input
                                        type="number"
                                        value={amount}
                                        onChange={(e) => setAmount(Number(e.target.value))}
                                        className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white font-mono font-bold focus:border-[#00ffa3] focus:ring-1 focus:ring-[#00ffa3] outline-none transition-all"
                                    />
                                </div>

                                <div className="flex items-center gap-3 p-3 bg-[#00ffa3]/5 rounded-xl border border-[#00ffa3]/10">
                                    <div
                                        onClick={() => setConfirmed(!confirmed)}
                                        className={`w-10 h-5 rounded-full relative cursor-pointer transition-colors duration-300 ${confirmed ? 'bg-[#00ffa3]' : 'bg-zinc-700'}`}
                                    >
                                        <div className={`w-3 h-3 rounded-full bg-black absolute top-1 transition-all duration-300 ${confirmed ? 'left-6' : 'left-1'}`} />
                                    </div>
                                    <span className="text-[10px] font-bold text-[#00ffa3] uppercase leading-tight">
                                        I confirm this is a human manual execution.
                                    </span>
                                </div>
                            </div>

                            <button
                                onClick={executeTrade}
                                disabled={!confirmed}
                                className={`w-full py-4 rounded-xl font-black uppercase tracking-widest text-sm flex items-center justify-center gap-2 transition-all duration-300
                                    ${confirmed
                                        ? 'bg-[#00ffa3] text-black hover:scale-[1.02] shadow-[0_0_20px_rgba(0,255,163,0.3)]'
                                        : 'bg-zinc-800 text-zinc-600 cursor-not-allowed'}
                                `}
                            >
                                <Zap size={16} className={confirmed ? "fill-black" : ""} />
                                {confirmed ? "Execute Now" : "Confirm to Unlock"}
                            </button>
                        </>
                    )}

                    {/* Processing State */}
                    {status === 'PROCESSING' && (
                        <div className="py-8 flex flex-col items-center justify-center gap-4 animate-in zoom-in">
                            <Loader2 className="animate-spin text-[#00ffa3]" size={40} />
                            <p className="text-xs font-mono text-[#00ffa3] animate-pulse">{log}</p>
                        </div>
                    )}

                    {/* Success State */}
                    {status === 'SUCCESS' && (
                        <div className="py-6 flex flex-col items-center justify-center gap-4 text-center animate-in zoom-in">
                            <div className="w-16 h-16 rounded-full bg-[#00ffa3]/10 flex items-center justify-center border border-[#00ffa3]/20">
                                <CheckCircle className="text-[#00ffa3]" size={32} />
                            </div>
                            <div>
                                <h3 className="text-lg font-black text-white mb-1">Execution Complete</h3>
                                <p className="text-xs text-zinc-500 font-mono">{log}</p>
                            </div>
                            <button onClick={onClose} className="mt-2 px-6 py-2 bg-white/5 hover:bg-white/10 rounded-full text-xs font-bold text-white transition">
                                Close
                            </button>
                        </div>
                    )}

                    {/* Error State */}
                    {status === 'ERROR' && (
                        <div className="py-6 flex flex-col items-center justify-center gap-4 text-center animate-in zoom-in">
                            <div className="w-16 h-16 rounded-full bg-red-500/10 flex items-center justify-center border border-red-500/20">
                                <AlertTriangle className="text-red-500" size={32} />
                            </div>
                            <div>
                                <h3 className="text-lg font-black text-white mb-1">Execution Failed</h3>
                                <p className="text-xs text-red-500 font-mono max-w-[200px] mx-auto break-words">{log}</p>
                            </div>
                            <button onClick={() => setStatus('IDLE')} className="mt-2 text-xs font-bold text-zinc-500 hover:text-white underline">
                                Try Again
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
