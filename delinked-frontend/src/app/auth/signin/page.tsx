'use client';

import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";

export default function SignIn() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/";

  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-6 py-12">
      <div className="mx-auto w-full max-w-sm">
        <h2 className="mt-6 text-center text-3xl font-bold tracking-tight">
          Sign in to your account
        </h2>
        <div className="mt-8">
          <button
            onClick={() => signIn('google', { callbackUrl })}
            className="flex w-full justify-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500"
          >
            Sign in with Google
          </button>
        </div>
      </div>
    </div>
  );
}