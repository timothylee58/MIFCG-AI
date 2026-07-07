import { createClient } from "@/lib/supabase/client";

/**
 * fetch() wrapper that attaches the current Supabase session's access token
 * as a Bearer Authorization header. The backend requires a valid Supabase
 * JWT on every non-health route, so any call to the API must go through
 * this instead of the raw fetch().
 */
export async function authedFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const headers = new Headers(init.headers);
  if (session?.access_token) {
    headers.set("Authorization", `Bearer ${session.access_token}`);
  }

  return fetch(input, { ...init, headers });
}
