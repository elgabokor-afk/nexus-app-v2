import { useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { Zap, ShieldCheck, AlertTriangle, CheckCircle, Loader2, X } from 'lucide-react';

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
    const [status, setStatus] = useState<'IDLE' | 'PROCESSING' | 'SUCCESS' | 'ERROR'>('IDLE');
    const [log, setLog] = useState<string>('');
    const [amount, setAmount] = useState<number>(100); // Default Trade Size USD

    const executeTrade = async () => {
        if (!confirmed) return;
        setStatus('PROCESSING');
        setLog('Initializing Secure Execution...');

        try {
            const { data: { user } } = await supabase.auth.getUser();
            if (!user) throw new Error("Authentication Required");

            setLog('Validating Credentials...');

            // Call Railway API
            // Note: Replace with your actual deployed Railway URL or Proxy
            const API_URL = process.env.NEXT_PUBLIC_EXECUTION_API_URL || "http://localhost:8000";

            setLog(`Sending Order to ${API_URL}...`);

            const res = await fetch(`${API_URL}/execute-trade`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${user.id}` // Simplified Auth
                },
                body: JSON.stringify({
                    user_id: user.id,
                    symbol: signal.symbol,
                    side: signal.side.toLowerCase(),
                    amount_usd: amount,
                    stop_loss: signal.stop_loss,
                    take_profit: signal.take_profit
                })
            });

            const data = await res.json();

            if (!res.ok) throw new Error(data.detail || "Execution Failed");

            setLog(`Order Filled! ID: ${data.order?.id}`);
            setStatus('SUCCESS');

        } catch (e: any) {
            setLog(`ERROR: ${e.message}`);
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

                {/* Body */}
                <div className="p-6 space-y-6">

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
                    </div>

                    {/* Controls */}
                    {status === 'IDLE' && (
                        <>
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

                                {/* Legal / Human Check */}
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
