"use client";

import { Gauge, Zap } from "lucide-react";

interface VolatilityProps {
    fngIndex: number;
    volatility?: number; // 0-100
}

export default function VolatilityGauge({ fngIndex, volatility = 50 }: VolatilityProps) {
    // FNG: 0 (Extreme Fear) -> 100 (Extreme Greed)
    // We want to color code it.
    // < 25: Extreme Fear (Green for buying? Or Red for panic?) -> Usually Red/Orange
    // > 75: Extreme Greed (Green)

    let color = "text-yellow-400";
    let status = "NEUTRAL";

    if (fngIndex < 25) { color = "text-red-500"; status = "EXTREME FEAR"; }
    else if (fngIndex < 45) { color = "text-orange-400"; status = "FEAR"; }
    else if (fngIndex > 75) { color = "text-green-500"; status = "EXTREME GREED"; }
    else if (fngIndex > 55) { color = "text-green-400"; status = "GREED"; }

    return (
        <div className="bg-[#0a0a0a] border border-white/10 rounded-xl p-4 flex flex-col gap-3 relative overflow-hidden group h-full">
            <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-gray-500 tracking-widest uppercase flex items-center gap-2">
                    <Zap size={14} className="text-[#00ffa3]" />
                    Market Sentiment
                </h3>
            </div>

            <div className="flex items-end justify-between mt-2">
                <div>
                    <span className="text-gray-400 text-[10px] font-bold block mb-1">FEAR & GREED</span>
                    <span className={`text-4xl font-black ${color} tracking-tighter`}>
                        {fngIndex}
                    </span>
                    <span className={`block text-[10px] font-bold ${color} mt-1`}>{status}</span>
                </div>

                {/* Mini Volatility Bars */}
                <div className="flex gap-1 items-end h-10 pb-1">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i}
                            className={`w-2 rounded-t-sm transition-all duration-500 ${i * 20 < fngIndex ? color.replace("text-", "bg-") : "bg-gray-800"}`}
                            style={{ height: `${i * 20}%` }}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
