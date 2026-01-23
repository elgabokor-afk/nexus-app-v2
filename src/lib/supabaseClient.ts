import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
    console.error('Supabase Env Vars status:', {
        url: !!supabaseUrl,
        key: !!supabaseAnonKey,
        NODE_ENV: process.env.NODE_ENV
    })
    console.warn("⚠️ SUPABASE CREDENTIALS MISSING - RUNNING IN MOCK MODE ⚠️");
}

// Safe Client Mock
const mockSupabase = {
    from: () => ({
        select: () => ({
            order: () => ({
                limit: () => Promise.resolve({ data: [], error: null })
            })
        }),
        insert: () => Promise.resolve({ error: null })
    }),
    channel: () => ({
        on: () => ({ subscribe: () => { } }),
        unsubscribe: () => { }
    }),
    removeChannel: () => { }
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
