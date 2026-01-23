import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
    // During build time, if vars are missing, we can log a warning instead of crashing
    // OR we provide a descriptive error
    console.error('Supabase Env Vars status:', {
        url: !!supabaseUrl,
        key: !!supabaseAnonKey,
        NODE_ENV: process.env.NODE_ENV
    })

    throw new Error(`Missing Supabase Environment Variables: ${!supabaseUrl ? 'NEXT_PUBLIC_SUPABASE_URL' : ''} ${!supabaseAnonKey ? 'NEXT_PUBLIC_SUPABASE_ANON_KEY' : ''}`)
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
