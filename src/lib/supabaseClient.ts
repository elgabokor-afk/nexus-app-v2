import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://uxjjqrctxfajzicruvxc.supabase.co"
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4ampxcmN0eGZhanppY3J1dnhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkwMjM1NjYsImV4cCI6MjA4NDU5OTU2Nn0.MyzhM7h5xM45SwtZ40DoaS_Cg6SMByuYVrBkmIhNYPM"

if (!supabaseUrl || !supabaseAnonKey) {
    console.error('Supabase Env Vars status:', {
        url: !!supabaseUrl,
        key: !!supabaseAnonKey,
        NODE_ENV: process.env.NODE_ENV
    })
    console.warn("⚠️ SUPABASE CREDENTIALS MISSING - RUNNING IN MOCK MODE ⚠️");
}

// Safe Client Mock with Proxy (Catches ALL methods)
const createMockClient = () => {
    return new Proxy({}, {
        get: (target, prop) => {
            // Return a function for any property access
            return (...args: any[]) => {
                // If it's a promise-like call (then/catch), return a promise
                if (prop === 'then') {
                    if (args.length > 0) return Promise.resolve({ data: [], error: null }).then(args[0]);
                    return Promise.resolve({ data: [], error: null });
                }

                // Special handling for subscriptions
                if (prop === 'on' || prop === 'subscribe' || prop === 'channel') {
                    return createMockClient(); // Return another proxy for chaining
                }

                // Default: return a promise that resolves to empty data (chainable)
                // We return the proxy itself to allow chaining like .from().select().eq()...
                // But wait, we need to return a Promise-like object that is ALSO a proxy? 
                // Simplification: Return an object that has 'then' and is also a proxy.

                const prom = Promise.resolve({ data: [], error: null });
                return new Proxy(prom, {
                    get: (targetPromise, childProp) => {
                        if (childProp === 'then' || childProp === 'catch' || childProp === 'finally') {
                            return (targetPromise as any)[childProp];
                        }
                        return createMockClient(); // Continue chaining for non-promise methods
                    }
                });
            };
        }
    });
};

const mockSupabase = {
    from: () => {
        // Return a chainable proxy for query building
        const queryBuilder: any = new Proxy(Promise.resolve({ data: [], error: null }), {
            get: (target, prop) => {
                if (prop === 'then' || prop === 'catch' || prop === 'finally') return (target as any)[prop];
                // Support ordinary methods like select, insert, eq, order, limit
                return (...args: any[]) => queryBuilder;
            }
        });
        return queryBuilder;
    },
    channel: () => ({
        on: () => ({ subscribe: () => { } }),
        unsubscribe: () => Promise.resolve()
    }),
    removeChannel: () => Promise.resolve()
} as any;

let clientToExport = mockSupabase;

if (supabaseUrl && supabaseAnonKey) {
    try {
        clientToExport = createClient(supabaseUrl, supabaseAnonKey);
    } catch (e) {
        console.error("Supabase Init Error:", e);
    }
}

export const supabase = clientToExport;
