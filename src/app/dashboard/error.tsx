
'use client';

import { useEffect } from 'react';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // Log the error to an error reporting service
        console.error('Dashboard Error:', error);
    }, [error]);

    return (
        <div className="flex h-screen items-center justify-center bg-[#050505] text-white p-4">
            <div className="max-w-md w-full border border-red-900/50 bg-red-950/10 rounded-xl p-8 text-center shadow-2xl">
                <h2 className="text-2xl font-bold text-red-500 mb-4 font-mono">CRITICAL ERROR</h2>
                <p className="text-gray-300 mb-6 font-mono text-sm leading-relaxed">
                    The dashboard encountered an unexpected issue.
                </p>

                <div className="bg-[#000] p-4 rounded text-left mb-6 overflow-auto max-h-40 border border-[#222]">
                    <p className="text-red-400 font-mono text-xs whitespace-pre-wrap break-all">
                        {error.message || "Unknown error occurred"}
                    </p>
                    {error.digest && <p className="text-gray-600 text-[10px] mt-2">Digest: {error.digest}</p>}
                </div>

                <button
                    onClick={reset}
                    className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-6 rounded transition-colors font-mono uppercase tracking-widest text-xs"
                >
                    Try Again
                </button>
            </div>
        </div>
    );
}
