
"use client";
import { useEffect, useState, useCallback } from 'react';

interface LivePayload {
    channel: string;
    data: any;
}

export function useLiveStream(channels: string[]) {
    const [lastMessage, setLastMessage] = useState<LivePayload | null>(null);
    const [isConnected, setIsConnected] = useState(false);

    const connect = useCallback(() => {
        // Use environment variable for WS URL or fallback to localhost
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/live";
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log("   [LIVE STREAM] Connected to Bridge.");
            setIsConnected(true);
        };

        socket.onmessage = (event) => {
            try {
                const payload: LivePayload = JSON.parse(event.data);
                if (channels.includes(payload.channel)) {
                    setLastMessage(payload);
                }
            } catch (err) {
                console.error("   [LIVE STREAM] Parse Error:", err);
            }
        };

        socket.onclose = () => {
            console.log("   [LIVE STREAM] Disconnected. Reconnecting...");
            setIsConnected(false);
            setTimeout(connect, 3000); // Reconnect loop
        };

        socket.onerror = (err) => {
            console.error("   [LIVE STREAM] Socket Error:", err);
            socket.close();
        };

        return socket;
    }, [channels]);

    useEffect(() => {
        const socket = connect();
        return () => {
            socket.close();
        };
    }, [connect]);

    return { lastMessage, isConnected };
}
