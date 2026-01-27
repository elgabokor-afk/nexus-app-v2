import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs';
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
    const supabase = createRouteHandlerClient({ cookies });

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
