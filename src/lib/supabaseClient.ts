import { createBrowserClient } from '@supabase/ssr'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "https://uxjjqrctxfajzicruvxc.supabase.co"
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4ampxcmN0eGZhanppY3J1dnhjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjkwMjM1NjYsImV4cCI6MjA4NDU5OTU2Nn0.MyzhM7h5xM45SwtZ40DoaS_Cg6SMByuYVrBkmIhNYPM"

export const supabase = createBrowserClient(supabaseUrl, supabaseAnonKey)
