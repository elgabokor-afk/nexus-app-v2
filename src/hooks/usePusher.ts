import { useEffect, useState } from 'react';
import Pusher from 'pusher-js';
import { useProfile } from './useProfile';

// V3600: Market Status Interface
interface MarketStatus {
    sentiment: "BULLISH" | "BEARISH" | "NEUTRAL" | "RISK_ON" | "RISK_OFF";
    active_expert?: string;
    regime?: string;
    expert_confidence?: number;
    dxy_change: number;
    spx_change: number;
    fng_index: number;
}

export function usePusher() {
    const { isVip } = useProfile();
    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'unavailable'>('connecting');
    const [marketStatus, setMarketStatus] = useState<MarketStatus>({
        sentiment: "NEUTRAL",
        active_expert: "PARRONDO (Game Theory)",
        regime: "LOW_VOLATILITY",
        expert_confidence: 88,
        dxy_change: 0,
        spx_change: 0,
        fng_index: 50
    });
    const [livePrices, setLivePrices] = useState<Record<string, number>>({});
    const [realtimeSignals, setRealtimeSignals] = useState<any[]>([]);

    // V2700: Auditor Updates
    const [auditUpdates, setAuditUpdates] = useState<any>(null);

    useEffect(() => {
        // V2100: PUSHER REALTIME CLIENT
        const pusher = new Pusher(process.env.NEXT_PUBLIC_PUSHER_KEY!, {
            cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
            authEndpoint: '/api/pusher/auth',
            forceTLS: true,
        });

        // 1. Connection Handling
        pusher.connection.bind('connected', () => {
            setConnectionStatus('connected');
            console.log('[Pusher] Bridge Active');
        });
        pusher.connection.bind('unavailable', () => setConnectionStatus('unavailable'));
        pusher.connection.bind('failed', () => setConnectionStatus('unavailable'));

        // 2. Public Channels
        const publicChannel = pusher.subscribe('public-signals');
        const marketChannel = pusher.subscribe('public-market-status');
        const priceChannel = pusher.subscribe('public-price-feed');

        // BIND: New Signals
        publicChannel.bind('new-signal', (data: any) => {
            console.log('⚡ [SIGNAL] Public:', data);
            setRealtimeSignals(prev => [data, ...prev].slice(0, 50));
        });

        // BIND: Auditor Updates
        publicChannel.bind('signal-update', (data: any) => {
            setAuditUpdates(data);
        });

        // BIND: Market Status (Macro + FnG)
        marketChannel.bind('macro-update', (data: any) => {
            setMarketStatus(prev => ({
                ...prev,
                sentiment: data.sentiment || prev.sentiment,
                active_expert: data.active_expert || prev.active_expert,
                regime: data.regime || prev.regime,
                expert_confidence: data.expert_confidence || prev.expert_confidence,
                dxy_change: data.dxy_change || prev.dxy_change,
                spx_change: data.spx_change || prev.spx_change,
                fng_index: data.fng_index || prev.fng_index
            }));
        });

        // BIND: Price Feed (High Frequency)
        priceChannel.bind('price-update', (data: any) => {
            if (data?.symbol && data?.price) {
                setLivePrices(prev => ({
                    ...prev,
                    [data.symbol]: Number(data.price)
                }));
            }
        });

        // 3. Private VIP Channel
        let privateChannel: any = null;
        if (isVip) {
            privateChannel = pusher.subscribe('private-vip-signals');
            privateChannel.bind('new-signal', (data: any) => {
                console.log('💎 [VIP] Signal:', data);
                // Audio Alert
                try {
                    new Audio('/sounds/signal_alert.mp3').play().catch(() => { });
                } catch (e) { }
                setRealtimeSignals(prev => [data, ...prev].slice(0, 50));
            });
        }

        // Cleanup
        return () => {
            pusher.unsubscribe('public-signals');
            pusher.unsubscribe('public-market-status');
            pusher.unsubscribe('public-price-feed');
            if (privateChannel) pusher.unsubscribe('private-vip-signals');
            pusher.disconnect();
        };

    }, [isVip]);

    return {
        connectionStatus,
        marketStatus,
        livePrices,
        realtimeSignals,
        auditUpdates
    };
}
