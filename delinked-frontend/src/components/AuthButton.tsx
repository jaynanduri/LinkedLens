'use client';

import { signIn, signOut, useSession } from "next-auth/react";

export default function AuthButton() {
  const { data: session, status } = useSession();
  const isLoading = status === "loading";

  if (isLoading) {
    return <button className="px-4 py-2 rounded bg-gray-200">Loading...</button>;
  }

  if (session) {
    return (
      <div className="flex items-center gap-4">
        <span>Signed in as {session.user?.email}</span>
        <button
          onClick={() => signOut()}
          className="px-4 py-2 rounded bg-red-500 text-white"
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => signIn("google")}
      className="px-4 py-2 rounded bg-blue-500 text-white"
    >
      Sign in with Google
    </button>
  );
}