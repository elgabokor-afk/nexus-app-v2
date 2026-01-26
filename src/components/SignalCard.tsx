
import React from 'react';
import { ArrowUpRight, ArrowDownRight, Activity, Brain, BarChart2 } from 'lucide-react';

interface SignalProps {
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
    imbalance?: number;
    depth_score?: number;
    onViewChart?: (symbol: string) => void;
    onConsultAI?: (signal: any) => void;
}

const SignalCard: React.FC<SignalProps & { compact?: boolean }> = ({
    symbol, price, rsi, signal_type, confidence, timestamp, stop_loss, take_profit, atr_value, volume_ratio, imbalance, depth_score, onViewChart, onConsultAI, compact = false
}) => {

    const isBuy = signal_type.includes('BUY');
    const isSell = signal_type.includes('SELL');
    const isNeutral = !isBuy && !isSell;

    const coin = symbol.split('/')[0];
    const logoUrl = `https://raw.githubusercontent.com/spothq/cryptocurrency-icons/master/128/color/${coin.toLowerCase()}.png`;

    let borderColor = 'border-gray-800';
    let textColor = 'text-gray-400';
    let actionText = 'WAITING';

    if (isBuy) {
        borderColor = 'border-[#00ffa3]';
        textColor = 'text-[#00ffa3]';
        actionText = 'LONG';
    } else if (isSell) {
        borderColor = 'border-[#ff4d4d]';
        textColor = 'text-[#ff4d4d]';
        actionText = 'SHORT';
    }

    const formatPrice = (p: number | undefined) =>
        p ? `$${Number(p).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '---';

    return (
        <div
            onClick={() => compact && onViewChart && onViewChart(symbol)}
            className={`
                relative overflow-hidden group transition-all duration-500
                ${compact ? 'p-3 pr-4 cursor-pointer hover:bg-white/5 border border-white/5 rounded-2xl hover:border-[#00ffa3]/30 transition-all active:scale-[0.98]' : 'p-0 backdrop-blur-xl bg-[#0a0a0c]/80 border border-white/5 rounded-3xl hover:border-white/10 hover:shadow-2xl hover:shadow-green-500/5'}
                ${isBuy && !compact ? 'shadow-[0_0_40px_-10px_rgba(0,255,163,0.15)]' : ''}
                ${isSell && !compact ? 'shadow-[0_0_40px_-10px_rgba(255,77,77,0.15)]' : ''}
                bg-gradient-to-br from-white/[0.03] to-transparent
            `}
        >
            {/* COMPACT MODE LAYOUT (Single Row Fluid) */}
            {compact ? (
                <div className="flex items-center justify-between gap-4">
                    {/* Left: Icon & Symbol */}
                    <div className="flex items-center gap-3 min-w-[120px]">
                        <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center p-1 border border-white/10">
                            <img src={logoUrl} alt={coin} className="w-full h-full object-contain"
                                onError={(e) => { (e.target as HTMLElement).style.display = 'none'; }}
                            />
                        </div>
                        <div>
                            <h3 className="text-sm font-bold text-white">{symbol}</h3>
                            <div className={`text-[10px] font-black ${textColor}`}>{actionText}</div>
                        </div>
                    </div>

                    {/* Middle: Price & Confidence */}
                    <div className="flex-1 flex flex-col items-end mr-2">
                        <span className="text-sm font-mono font-bold text-white tracking-tight">{formatPrice(price)}</span>
                        <div className="flex items-center gap-1">
                            <div className="w-12 h-1 bg-white/10 rounded-full overflow-hidden">
                                <div className={`h-full ${isBuy ? 'bg-[#00ffa3]' : 'bg-[#ff4d4d]'}`} style={{ width: `${confidence}%` }}></div>
                            </div>
                            <span className="text-[9px] text-gray-500 font-mono">{confidence}%</span>
                        </div>
                    </div>

                    {/* Right: Actions (No Overlap) */}
                    <div className="flex items-center gap-2 pl-3 border-l border-white/5">
                        {onConsultAI && (
                            <button
                                onClick={(e) => { e.stopPropagation(); onConsultAI({ symbol, price, confidence, signal_type, rsi, stop_loss, take_profit }); }}
                                className="p-2 rounded-lg bg-purple-500/10 text-purple-400 hover:bg-purple-500 hover:text-white transition-all shadow-[0_0_10px_rgba(168,85,247,0.0)] hover:shadow-[0_0_10px_rgba(168,85,247,0.4)]"
                                title="Consult AI"
                            >
                                <Brain size={14} />
                            </button>
                        )}
                        <button className="p-2 rounded-lg bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white transition-colors">
                            <BarChart2 size={14} />
                        </button>
                    </div>
                </div>
            ) : (
                /* FULL MODE LAYOUT (Spacious) */
                <>
                    {/* Header */}
                    <div className="p-6 flex justify-between items-start">
                        <div className="flex items-center gap-4">
                            <div className="relative">
                                <div className="w-14 h-14 flex items-center justify-center rounded-2xl p-1 overflow-hidden bg-white/[0.05] border border-white/10">
                                    <img src={logoUrl} alt={coin} className="w-full h-full object-contain" />
                                </div>
                                {confidence > 85 && (
                                    <div className="absolute -top-1 -right-1 w-3 h-3 bg-[#00ffa3] rounded-full shadow-[0_0_10px_#00ffa3] border-2 border-[#0a0a0c]"></div>
                                )}
                            </div>
                            <div>
                                <h3 className="text-xl font-bold font-sans text-white tracking-tight">{symbol}</h3>
                                <div className="flex items-center gap-2 mt-0.5">
                                    <span className={`text-[10px] font-black tracking-widest uppercase ${textColor}`}>{actionText}</span>
                                    <span className="text-[10px] text-white/20 font-mono">•</span>
                                    <span className="text-[10px] text-gray-500 font-medium">{confidence}% Conf.</span>
                                </div>
                            </div>
                        </div>

                        <div className="text-right">
                            <p className="text-2xl font-mono font-bold text-white tracking-tighter">{formatPrice(price)}</p>
                            <div className="flex items-center justify-end gap-1.5 mt-1">
                                <Activity size={12} className={rsi < 30 || rsi > 70 ? textColor : 'text-gray-600'} />
                                <span className={`text-[10px] font-mono ${rsi < 30 || rsi > 70 ? 'text-white' : 'text-gray-500'}`}>RSI: {rsi}</span>
                            </div>
                        </div>
                    </div>

                    {/* Stats Grid */}
                    <div className="px-6 pb-6">
                        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-3 flex items-center justify-between">
                            <div className="space-y-1">
                                <p className="text-[9px] uppercase tracking-widest text-gray-500 font-bold">Vol</p>
                                <p className="text-xs font-medium text-white">{(volume_ratio || 0).toFixed(2)}x</p>
                            </div>
                            <div className="h-6 w-px bg-white/5"></div>
                            <div className="space-y-1">
                                <p className="text-[9px] uppercase tracking-widest text-gray-500 font-bold">ATR</p>
                                <p className="text-xs font-medium text-white">{(atr_value || 0).toFixed(2)}</p>
                            </div>
                            <div className="h-6 w-px bg-white/5"></div>
                            <div className="space-y-1 text-right">
                                <p className="text-[9px] uppercase tracking-widest text-[#00ffa3] font-bold">TP</p>
                                <p className="text-xs font-mono text-white font-bold">{formatPrice(take_profit)}</p>
                            </div>
                        </div>
                    </div>

                    {/* Footer Actions (New Row) */}
                    <div className="p-4 bg-black/40 border-t border-white/5 flex gap-3">
                        <button
                            onClick={() => onViewChart && onViewChart(symbol)}
                            className={`
                                flex-1 py-3 rounded-xl font-black text-[10px] tracking-[0.2em] uppercase
                                transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]
                                ${isBuy ? 'bg-[#00ffa3] text-black hover:bg-white' : 'bg-[#ff4d4d] text-white hover:bg-white hover:text-black'}
                            `}
                        >
                            Analyze
                        </button>

                        {onConsultAI && (
                            <button
                                onClick={(e) => { e.stopPropagation(); onConsultAI({ symbol, price, confidence, signal_type, rsi, stop_loss, take_profit }); }}
                                className="px-4 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 hover:bg-purple-500 hover:text-white transition-all flex items-center gap-2 group/ai"
                            >
                                <Brain size={16} className="group-hover/ai:animate-pulse" />
                                <span className="hidden sm:inline text-[10px] font-bold uppercase tracking-wider">Ask AI</span>
                            </button>
                        )}
                    </div>
                </>
            )}
        </div>
    );
};

export default SignalCard;
