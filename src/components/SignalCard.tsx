
import React from 'react';
import { ArrowUpRight, ArrowDownRight, Activity, Brain } from 'lucide-react';

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

    // Logic must be INSIDE the component
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
                ${compact ? 'p-4 cursor-pointer hover:bg-white/5 border border-white/5 rounded-2xl hover:border-[#00ffa3]/30 transition-all active:scale-[0.98]' : 'p-0 backdrop-blur-xl bg-[#0a0a0c]/80 border border-white/5 rounded-3xl hover:border-white/10 hover:shadow-2xl hover:shadow-green-500/5'}
                ${isBuy && !compact ? 'shadow-[0_0_40px_-10px_rgba(0,255,163,0.15)]' : ''}
                ${isSell && !compact ? 'shadow-[0_0_40px_-10px_rgba(255,77,77,0.15)]' : ''}
                bg-gradient-to-br from-white/[0.03] to-transparent
            `}
        >
            {/* V1600: Consult AI Button (Absolute Top-Right) */}
            <div className="absolute top-4 right-4 z-20 flex gap-2">
                {onConsultAI && (
                    <button
                        onClick={(e) => { e.stopPropagation(); onConsultAI({ symbol, price, confidence, signal_type, rsi, stop_loss, take_profit }); }}
                        className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 hover:bg-purple-500/20 hover:text-purple-300 transition-colors backdrop-blur-md border border-purple-500/20"
                        title="Consult AI Expert"
                    >
                        <Brain size={compact ? 14 : 16} />
                    </button>
                )}
            </div>

            {/* Header / Main Info */}
            <div className={`${compact ? 'flex justify-between items-start' : 'p-6 flex justify-between items-start'}`}>
                <div className="flex items-center gap-4">
                    <div className="relative">
                        <div className={`
                            flex items-center justify-center rounded-2xl p-1 overflow-hidden
                            ${compact ? 'w-10 h-10' : 'w-14 h-14'}
                            bg-white/[0.05] border border-white/10
                        `}>
                            <img
                                src={logoUrl}
                                alt={coin}
                                className="w-full h-full object-contain"
                                onError={(e) => {
                                    (e.target as HTMLImageElement).style.display = 'none';
                                    (e.target as HTMLImageElement).parentElement!.classList.add('flex', 'items-center', 'justify-center', 'font-bold', 'text-white');
                                    (e.target as HTMLImageElement).parentElement!.innerText = coin.substring(0, 1);
                                }}
                            />
                        </div>
                        {confidence > 85 && (
                            <div className="absolute -top-1 -right-1 w-3 h-3 bg-[#00ffa3] rounded-full shadow-[0_0_10px_#00ffa3] border-2 border-[#0a0a0c]"></div>
                        )}
                    </div>

                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className={`${compact ? 'text-sm' : 'text-xl'} font-bold font-sans text-white tracking-tight`}>{symbol}</h3>
                            {/* Vol Badge */}
                            {(volume_ratio || 0) > 1.2 && <span className="px-1.5 py-0.5 rounded-[4px] text-[8px] font-black bg-blue-500 text-black uppercase tracking-tighter">High Vol</span>}
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                            <span className={`text-[10px] font-black tracking-widest uppercase ${textColor}`}>
                                {actionText}
                            </span>
                            <span className="text-[10px] text-white/20 font-mono">•</span>
                            <span className="text-[10px] text-gray-500 font-medium">{confidence}% Conf.</span>
                        </div>
                    </div>
                </div>

                <div className="text-right pr-8">
                    <p className={`${compact ? 'text-sm' : 'text-2xl'} font-mono font-bold text-white tracking-tighter`}>
                        {formatPrice(price)}
                    </p>
                    <div className="flex items-center justify-end gap-1.5 mt-1">
                        <Activity size={10} className={rsi < 30 || rsi > 70 ? textColor : 'text-gray-600'} />
                        <span className={`text-[10px] font-mono ${rsi < 30 || rsi > 70 ? 'text-white' : 'text-gray-500'}`}>RSI: {rsi}</span>
                    </div>
                </div>
            </div>

            {/* AI Reasoning / Logic Breakdown */}
            <div className={`px-4 pb-2 pt-1 ${compact ? 'block' : 'px-6 pb-6'}`}>
                <div className="bg-white/[0.02] border border-white/5 rounded-xl p-2.5 flex items-center justify-between">
                    <div>
                        <p className="text-[8px] text-gray-500 uppercase tracking-widest font-bold">Vol Pressure</p>
                        <p className={`text-[11px] font-medium ${(volume_ratio || 0) > 1 ? 'text-white' : 'text-gray-500'}`}>
                            {(volume_ratio || 0).toFixed(2)}x
                        </p>
                    </div>
                    <div className="h-6 w-px bg-white/5 mx-3"></div>
                    <div>
                        <p className="text-[8px] text-gray-500 uppercase tracking-widest font-bold">ATR Risk</p>
                        <p className="text-[11px] text-gray-300 font-medium">{(atr_value || 0).toFixed(2)}</p>
                    </div>
                    <div className="h-6 w-px bg-white/5 mx-3"></div>
                    <div className="flex-1">
                        <p className="text-[8px] text-gray-500 uppercase tracking-widest font-bold">Trend Status</p>
                        <div className="flex items-center gap-2 mt-0.5">
                            <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
                                <div
                                    className={`h-full ${isBuy ? 'bg-[#00ffa3]' : isSell ? 'bg-[#ff4d4d]' : 'bg-gray-600'} transition-all duration-1000 ease-out`}
                                    style={{ width: `${confidence}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* V4 QUANT: MARKET PRESSURE BAR */}
            {imbalance !== undefined && (
                <div className={`px-4 pb-4 ${compact ? 'block' : 'px-6'}`}>
                    <div className="flex justify-between items-end mb-1">
                        <p className="text-[9px] uppercase tracking-widest text-gray-500 font-bold flex items-center gap-1">
                            Market Pressure
                            {depth_score && depth_score > 50 && <span className="text-[8px] text-[#00ffa3] bg-[#00ffa3]/10 px-1 rounded">DEEP</span>}
                        </p>
                        <p className={`text-[9px] font-mono font-bold ${imbalance > 0 ? 'text-[#00ffa3]' : 'text-red-500'}`}>
                            {imbalance > 0 ? 'BULLISH' : 'BEARISH'} ({(imbalance * 100).toFixed(0)}%)
                        </p>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full relative overflow-hidden flex">
                        <div className="w-1/2 h-full bg-gradient-to-l from-transparent to-red-500/50"></div>
                        <div className="w-1/2 h-full bg-gradient-to-r from-transparent to-[#00ffa3]/50"></div>

                        {/* Indicator */}
                        <div
                            className="absolute top-0 bottom-0 w-1 bg-white shadow-[0_0_5px_white] transition-all duration-500"
                            style={{ left: `${((imbalance + 1) / 2) * 100}%` }}
                        ></div>
                    </div>
                </div>
            )}

            {/* Metrics Row */}
            {!isNeutral && (
                <div className={`
                    ${compact ? 'mt-2 p-3 bg-black/40 border-t border-white/5 grid grid-cols-2 gap-4' : 'px-6 py-5 grid grid-cols-2 gap-6 border-t border-white/5 bg-black/40'}
                `}>
                    <div className="space-y-1">
                        <p className="text-[9px] uppercase tracking-widest text-gray-500 font-bold">Target Stop</p>
                        <p className={`${compact ? 'text-xs' : 'text-base'} font-mono text-gray-400 font-medium`}>{formatPrice(stop_loss)}</p>
                    </div>
                    <div className="space-y-1 text-right">
                        <p className="text-[9px] uppercase tracking-widest text-[#00ffa3] font-bold">Target Profit</p>
                        <p className={`${compact ? 'text-xs' : 'text-base'} font-mono text-white font-bold`}>{formatPrice(take_profit)}</p>
                    </div>
                </div>
            )}

            {/* Footer Action (Full Mode Only) */}
            {!compact && !isNeutral && (
                <div className="p-6 pt-0">
                    <button
                        onClick={() => onViewChart && onViewChart(symbol)}
                        className={`
                            relative w-full py-4 rounded-2xl font-black text-[10px] tracking-[0.25em] uppercase overflow-hidden
                            transition-all duration-300 active:scale-[0.97]
                            ${isBuy
                                ? 'bg-[#00ffa3] text-black hover:bg-white shadow-[0_10px_30px_-10px_rgba(0,255,163,0.5)]'
                                : 'bg-[#ff4d4d] text-white hover:bg-white hover:text-black shadow-[0_10px_30px_-10px_rgba(255,77,77,0.5)]'}
                        `}
                    >
                        EXECUTE ANALYSIS
                    </button>
                </div>
            )}
        </div>
    );
};

export default SignalCard;
