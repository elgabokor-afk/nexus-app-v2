import React from 'react';
import { ArrowUpRight, ArrowDownRight, Activity } from 'lucide-react';

interface SignalProps {
    symbol: string;
    price: number;
    rsi: number;
    signal_type: string;
    confidence: number;
    timestamp: string;
    stop_loss?: number;
    take_profit?: number;
    onViewChart?: (symbol: string) => void;
}

const SignalCard: React.FC<SignalProps> = ({ symbol, price, rsi, signal_type, confidence, timestamp, stop_loss, take_profit, onViewChart }) => {
    const isBuy = signal_type.includes('BUY');
    const isSell = signal_type.includes('SELL');
    const isNeutral = !isBuy && !isSell;

    let borderColor = 'border-gray-800';
    let textColor = 'text-gray-400';
    let badgeBg = 'bg-gray-800';
    let actionText = 'WAITING';

    if (isBuy) {
        borderColor = 'border-[#00ffa3]';
        textColor = 'text-[#00ffa3]';
        badgeBg = 'bg-[#00ffa3]/10';
        actionText = 'LONG ENTRY';
    } else if (isSell) {
        borderColor = 'border-[#ff4d4d]';
        textColor = 'text-[#ff4d4d]';
        badgeBg = 'bg-[#ff4d4d]/10';
        actionText = 'SHORT ENTRY';
    }

    const formatPrice = (p: number | undefined) =>
        p ? `$${Number(p).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '---';

    return (
        <div className={`bg-[#0a0a0c] border border-opacity-40 ${borderColor} rounded-lg p-0 overflow-hidden hover:shadow-2xl hover:shadow-${isBuy ? 'green' : isSell ? 'red' : 'gray'}-500/10 transition-all duration-300 group`}>
            {/* Header */}
            <div className="p-5 border-b border-gray-800 flex justify-between items-center bg-[#111]">
                <div className="flex items-center gap-3">
                    <div className={`w-2 h-8 rounded-full ${isBuy ? 'bg-[#00ffa3]' : isSell ? 'bg-[#ff4d4d]' : 'bg-gray-600'}`}></div>
                    <div>
                        <h3 className="text-xl font-bold font-mono text-white tracking-wider">{symbol}</h3>
                        <p className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">
                            {new Date(timestamp).toLocaleTimeString()} • {confidence}% CONFIDENCE
                        </p>
                        <p className={`text-xs font-bold mt-1 ${textColor}`}>
                            {signal_type.split('(')[0].trim()}
                        </p>
                    </div>
                </div>
                <div className={`px-3 py-1 rounded text-xs font-bold ${textColor} ${badgeBg} border border-current border-opacity-20`}>
                    {actionText}
                </div>
            </div>

            {/* Metrics Grid */}
            <div className="p-5 grid grid-cols-2 gap-y-4 gap-x-8">
                <div>
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">Entry Price</p>
                    <p className="text-lg font-mono text-white font-medium">{formatPrice(price)}</p>
                </div>
                <div className="text-right">
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">RSI (14)</p>
                    <div className="flex items-center justify-end gap-2">
                        <span className={`font-bold font-mono ${rsi < 30 ? 'text-[#00ffa3]' : rsi > 70 ? 'text-[#ff4d4d]' : 'text-gray-300'}`}>
                            {rsi}
                        </span>
                        <Activity size={14} className="text-gray-600" />
                    </div>
                </div>

                {/* SL / TP Section */}
                {!isNeutral && (
                    <>
                        <div className="col-span-2 h-px bg-gray-800 my-1"></div>

                        <div>
                            <p className="text-[10px] text-red-500 uppercase tracking-wider mb-1 flex items-center gap-1">
                                Stop Loss <span className="opacity-50 text-[9px]">(Estimated)</span>
                            </p>
                            <p className="text-sm font-mono text-red-400">{formatPrice(stop_loss)}</p>
                        </div>
                        <div className="text-right">
                            <p className="text-[10px] text-[#00ffa3] uppercase tracking-wider mb-1 flex items-center justify-end gap-1">
                                Take Profit <span className="opacity-50 text-[9px]">(Target)</span>
                            </p>
                            <p className="text-sm font-mono text-[#00ffa3]">{formatPrice(take_profit)}</p>
                        </div>
                    </>
                )}
            </div>

            {/* Action Footer */}
            {!isNeutral && (
                <div className="p-4 bg-[#111] border-t border-gray-800">
                    <button
                        onClick={() => onViewChart && onViewChart(symbol)}
                        className={`w-full py-3 rounded font-bold text-sm tracking-widest uppercase transition-colors flex items-center justify-center gap-2 ${isBuy ? 'bg-[#00ffa3] text-black hover:bg-[#00cc82]' : 'bg-[#ff4d4d] text-white hover:bg-[#cc0000]'}`}
                    >
                        {isBuy ? <ArrowUpRight size={18} /> : <ArrowDownRight size={18} />}
                        VIEW LIVE CHART
                    </button>
                    <p className="text-[9px] text-center text-gray-600 mt-2">
                        Automated Analysis • Not Financial Advice
                    </p>
                </div>
            )}
        </div>
    );
};

export default SignalCard;
