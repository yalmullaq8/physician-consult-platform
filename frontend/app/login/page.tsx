"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { getCurrentUser, loginUser } from "@/lib/api";

function sanitizeNextPath(value: string | null): string {
  if (!value || !value.startsWith("/")) {
    return "/dashboard";
  }
  return value;
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const nextPath = useMemo(
    () => sanitizeNextPath(searchParams.get("next")),
    [searchParams],
  );

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function checkExistingSession() {
      const session = await getCurrentUser();
      if (!mounted) {
        return;
      }

      if (session.success) {
        router.replace(nextPath);
      }
    }

    checkExistingSession();
    return () => {
      mounted = false;
    };
  }, [nextPath, router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");
    setIsSubmitting(true);

    const result = await loginUser({ email, password });
    if (!result.success) {
      setErrorMessage(result.errorMessage ?? "Login failed.");
      setIsSubmitting(false);
      return;
    }

    router.replace(nextPath);
  }

  return (
    <div className="container-shell flex flex-1 items-center justify-center py-10 md:py-16">
      <section className="surface-card w-full max-w-md p-6 md:p-8">
        <p className="text-xs font-semibold tracking-[0.16em] text-[#3f493e] uppercase">Account Access</p>
        <h1 className="title-serif mt-2 text-3xl font-semibold text-[#1b1b1b]">Sign In</h1>
        <p className="mt-2 text-sm text-[#3f493e]">
          Sign in with your physician account to access your dashboard and availability tools.
        </p>

        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <label htmlFor="email" className="mb-1 block text-xs font-semibold tracking-[0.08em] text-[#3f493e] uppercase">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="w-full rounded-xl border border-[#bfcabb] bg-white px-3 py-2.5 text-sm text-[#1b1b1b] outline-none ring-[#00501e] transition focus:ring-2"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1 block text-xs font-semibold tracking-[0.08em] text-[#3f493e] uppercase">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="w-full rounded-xl border border-[#bfcabb] bg-white px-3 py-2.5 text-sm text-[#1b1b1b] outline-none ring-[#00501e] transition focus:ring-2"
              placeholder="Enter your password"
            />
          </div>

          {errorMessage ? (
            <div className="rounded-xl border border-[#efc4c4] bg-[#fff4f4] px-3 py-2 text-sm text-[#8a2d2d]">
              {errorMessage}
            </div>
          ) : null}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-xl bg-[#00501e] px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-[#006b2b] disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isSubmitting ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="mt-4 text-xs text-[#3f493e]">
          Need to browse dentists first? <Link href="/dentists" className="font-semibold text-[#00501e]">Go to directory</Link>
        </p>
      </section>
    </div>
  );
}
