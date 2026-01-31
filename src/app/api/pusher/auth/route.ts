import { createServerClient, type CookieOptions } from '@supabase/ssr';
import { cookies } from 'next/headers';
import { NextResponse } from 'next/server';
import Pusher from 'pusher';

const pusher = new Pusher({
    appId: process.env.PUSHER_APP_ID!,
    key: process.env.NEXT_PUBLIC_PUSHER_KEY!,
    secret: process.env.PUSHER_SECRET!,
    cluster: process.env.NEXT_PUBLIC_PUSHER_CLUSTER!,
    useTLS: true,
});

export async function POST(req: Request) {
    const cookieStore = await cookies();

    const supabase = createServerClient(
        process.env.NEXT_PUBLIC_SUPABASE_URL!,
        process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
        {
            cookies: {
                get(name: string) {
                    return cookieStore.get(name)?.value
                },
                set(name: string, value: string, options: CookieOptions) {
                    // Read-only for this route usually, but required by type
                },
                remove(name: string, options: CookieOptions) {
                    // Read-only
                },
            },
        }
    );

    // 1. Verify User Session
    const { data: { session } } = await supabase.auth.getSession();

    if (!session) {
        return new NextResponse('Unauthorized', { status: 401 });
    }

    // 2. Parse Body (socket_id, channel_name)
    const data = await req.formData();
    const socketId = data.get('socket_id') as string;
    const channel = data.get('channel_name') as string;

    // 3. Authorization Logic
    if (channel === 'private-vip-signals') {
        // Check VIP Status from DB
        const { data: profile } = await supabase
            .from('profiles')
            .select('subscription_level')
            .eq('id', session.user.id)
            .single();

        if (profile?.subscription_level !== 'vip') {
            return new NextResponse('Forbidden: VIP Only', { status: 403 });
        }
    }

    // 4. Authenticate with Pusher
    const authResponse = pusher.authenticate(socketId, channel);
    return NextResponse.json(authResponse);
}
