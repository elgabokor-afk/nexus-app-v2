import { createBrowserClient } from '@supabase/ssr'

// Validate required environment variables (only at runtime, not build time)
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || ''
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || ''

// Only validate in browser (not during build)
if (typeof window !== 'undefined' && (!supabaseUrl || !supabaseAnonKey)) {
    console.error(
        'Missing Supabase environment variables. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY in Railway dashboard.'
    )
}

export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey)
