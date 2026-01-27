'use client';

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabaseClient';
import { User, AuthChangeEvent, Session } from '@supabase/supabase-js';

export interface Profile {
    id: string;
    email: string;
    subscription_level: 'free' | 'vip';
    created_at: string;
}

export function useProfile() {
    const [user, setUser] = useState<User | null>(null);
    const [profile, setProfile] = useState<Profile | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let mounted = true;

        const getProfile = async () => {
            const { data: { session } } = await supabase.auth.getSession();

            if (session?.user) {
                if (mounted) setUser(session.user);

                const { data, error } = await supabase
                    .from('profiles')
                    .select('*')
                    .eq('id', session.user.id)
                    .single();

                if (data && mounted) {
                    setProfile(data);
                }
            }
            if (mounted) setLoading(false);
        };

        getProfile();

        const { data: { subscription } } = supabase.auth.onAuthStateChange((_event: AuthChangeEvent, session: Session | null) => {
            if (session?.user) {
                setUser(session.user);
                // Re-fetch profile on auth change
                supabase
                    .from('profiles')
                    .select('*')
                    .eq('id', session.user.id)
                    .single()
                    .then(({ data }) => {
                        if (mounted && data) setProfile(data);
                    });
            } else {
                if (mounted) {
                    setUser(null);
                    setProfile(null);
                }
            }
        });

        return () => {
            mounted = false;
            subscription.unsubscribe();
        };
    }, []);

    return { user, profile, loading, isVip: profile?.subscription_level === 'vip' };
}
