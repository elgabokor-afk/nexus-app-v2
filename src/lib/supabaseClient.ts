import { createBrowserClient } from '@supabase/ssr'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://uxjjqrctxfajzicruvxc.supabase.co"
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "tu_anon_key_aqui"

export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey)
