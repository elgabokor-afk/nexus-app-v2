/**
 * Environment Variable Validation Utility
 * Ensures all required environment variables are present before the app starts
 */

interface EnvConfig {
    // Supabase
    NEXT_PUBLIC_SUPABASE_URL: string
    NEXT_PUBLIC_SUPABASE_ANON_KEY: string

    // Pusher (Real-time)
    NEXT_PUBLIC_PUSHER_KEY: string
    NEXT_PUBLIC_PUSHER_CLUSTER: string

    // Optional: Backend API URL (has Railway internal fallback)
    NEXT_PUBLIC_API_URL?: string
}

export function validateEnv(): EnvConfig {
    const required = {
        NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
        NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
        NEXT_PUBLIC_PUSHER_KEY: process.env.NEXT_PUBLIC_PUSHER_KEY,
        NEXT_PUBLIC_PUSHER_CLUSTER: process.env.NEXT_PUBLIC_PUSHER_CLUSTER,
    }

    const missing: string[] = []

    for (const [key, value] of Object.entries(required)) {
        if (!value || value.trim() === '') {
            missing.push(key)
        }
    }

    if (missing.length > 0) {
        throw new Error(
            `Missing required environment variables:\n${missing.join('\n')}\n\n` +
            `Please configure these in your Railway dashboard under the frontend service.`
        )
    }

    return {
        ...required as Required<typeof required>,
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    }
}

// Validate on module load (client-side only)
if (typeof window !== 'undefined') {
    try {
        validateEnv()
    } catch (error) {
        console.error('❌ Environment validation failed:', error)
    }
}
