"use client";

import { useEffect, useState } from "react";
import { createClient } from "@supabase/supabase-js";

// --- Components ---

function MetricCard({ title, value, unit, status }: { title: string, value: string | number, unit?: string, status: "good" | "warn" | "bad" }) {
    const colors = {
        good: "border-green-500/50 text-green-400",
        warn: "border-yellow-500/50 text-yellow-400",
        bad: "border-red-500/50 text-red-400",
    };

    return (
        <div className={`p-4 rounded-xl bg-[#0a0a0a] border ${colors[status]} flex flex-col items-center justify-center gap-2`}>
            <span className="text-xs text-zinc-500 uppercase tracking-wider">{title}</span>
            <span className="text-3xl font-mono font-bold">
                {value}<span className="text-sm font-normal text-zinc-600 ml-1">{unit}</span>
            </span>
        </div>
    );
}

function ServiceStatus({ name, active }: { name: string, active: boolean }) {
    return (
        <div className="flex items-center justify-between p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
            <span className="font-mono text-zinc-300">{name}</span>
            <div className={`flex items-center gap-2 px-2 py-1 rounded text-xs font-bold ${active ? "bg-green-900/20 text-green-400 border border-green-500/30" : "bg-red-900/20 text-red-400 border border-red-500/30"}`}>
                <div className={`w-2 h-2 rounded-full ${active ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
                {active ? "ONLINE" : "OFFLINE"}
            </div>
        </div>
    );
}

export default function SystemAdminPage() {
    const [metrics, setMetrics] = useState({
        lps: 0,
        cacheHitRate: 0,
        dbLatency: 0,
        activeSignals: 0,
    });

    // Mock Realtime Data Refresh
    useEffect(() => {
        const interval = setInterval(() => {
            setMetrics({
                lps: Math.floor(Math.random() * (45 - 30) + 30), // 30-45 Lookups/sec
                cacheHitRate: 98.2, // 98% Cache Hit
                dbLatency: Math.floor(Math.random() * (120 - 40) + 40), // 40-120ms
                activeSignals: 12, // Mock
            });
        }, 2000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="min-h-screen bg-black text-white p-8 font-sans">
            <header className="mb-8 border-b border-zinc-800 pb-4">
                <h1 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-400 to-indigo-500 bg-clip-text text-transparent">
                    Cosmos Engineering Deck
                </h1>
                <p className="text-zinc-500 text-sm mt-1">Real-time System Performance & Health Monitor</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <MetricCard
                    title="RAG Lookups / Sec"
                    value={metrics.lps}
                    unit="LPS"
                    status={metrics.lps > 20 ? "good" : "warn"}
                />
                <MetricCard
                    title="Redis Cache Hit Rate"
                    value={metrics.cacheHitRate}
                    unit="%"
                    status={metrics.cacheHitRate > 90 ? "good" : "bad"}
                />
                <MetricCard
                    title="Vector DB Latency"
                    value={metrics.dbLatency}
                    unit="ms"
                    status={metrics.dbLatency < 200 ? "good" : "warn"}
                />
                <MetricCard
                    title="Active Signals"
                    value={metrics.activeSignals}
                    unit="LIVE"
                    status="good"
                />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

                {/* Service Health */}
                <div className="p-6 rounded-2xl border border-zinc-800 bg-[#050505]">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <span className="text-blue-500">◆</span> Microservices Status
                    </h3>
                    <div className="space-y-3">
                        <ServiceStatus name="cosmos-brain-processor" active={true} />
                        <ServiceStatus name="market-ingestion-engine" active={true} />
                        <ServiceStatus name="redis-cache-layer (v7)" active={true} />
                        <ServiceStatus name="pusher-notifier-bridge" active={true} />
                        <ServiceStatus name="academic-vector-validator" active={true} />
                    </div>
                </div>

                {/* System Logs (Mock) */}
                <div className="p-6 rounded-2xl border border-zinc-800 bg-[#050505] font-mono text-xs overflow-hidden">
                    <h3 className="text-lg font-bold mb-4 flex items-center gap-2 font-sans">
                        <span className="text-purple-500">◆</span> Live Kernel Logs
                    </h3>
                    <div className="flex flex-col gap-2 text-zinc-400 h-[240px] overflow-y-auto">
                        <div className="text-green-500">[INFO] RAG: Validated 'BTC/USDT' against 'Easley_OHara_2012.pdf' (Score: 0.92)</div>
                        <div className="text-blue-500">[CACHE] Redis: SET price:BTC value=64200.50 TTL=60s</div>
                        <div className="text-zinc-500">[DEBUG] VPIN calculation: 0.24 (Safe flow)</div>
                        <div className="text-yellow-500">[WARN] Liquidity: Depth on PEPE is low ($42,000). Filter active.</div>
                        <div className="text-green-500">[INFO] Brain: Signal generated. ID: sig_99283 - Confidence 89%</div>
                        <div className="text-zinc-500">[DEBUG] Worker: Broadcasting via Pusher... [OK]</div>
                        <div className="text-green-500">[INFO] RAG: Validated 'ETH/USDT' against 'Almgren_Chriss_2000.pdf' (Score: 0.88)</div>
                    </div>
                </div>

            </div>
        </div>
    );
}
