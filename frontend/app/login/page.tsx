"use client";

import { Suspense, useEffect, useState } from "react";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import LoginForm from "@/components/app-shell/LoginForm";

const DOWNLOADS: Record<string, string | null> = {
  mac: "/downloads/ZeroDelay-mac.dmg",
  pc: null, // TODO: no Windows build yet — see DownloadCta.tsx note.
};

function LoginContent() {
  const searchParams = useSearchParams();
  const os = searchParams.get("os") === "pc" ? "pc" : "mac";
  const [authenticated, setAuthenticated] = useState(false);
  const downloadHref = DOWNLOADS[os];

  useEffect(() => {
    if (authenticated && downloadHref) {
      // TODO: real integration — once there's a backend, this should hit an
      // authenticated download endpoint instead of a static public file.
      window.location.href = downloadHref;
    }
  }, [authenticated, downloadHref]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-page px-6">
      <Image src="/logo.png" alt="ZeroDelay" width={177} height={50} className="mb-4" />

      {!authenticated ? (
        <>
          <p className="mb-8 text-sm text-secondary">
            Sign in to download ZeroDelay for {os === "mac" ? "macOS" : "Windows"}
          </p>
          <LoginForm onSuccess={() => setAuthenticated(true)} submitLabel="Sign in & download" />
        </>
      ) : downloadHref ? (
        <div className="max-w-sm text-center">
          <p className="text-sm text-secondary">
            Your download should start automatically. If it doesn't,{" "}
            <a href={downloadHref} download className="font-medium text-accent-600 underline">
              click here
            </a>
            .
          </p>
        </div>
      ) : (
        <div className="max-w-sm text-center">
          <p className="text-sm text-secondary">
            You're signed in, but the Windows build isn't packaged yet — check
            back soon.
          </p>
        </div>
      )}
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginContent />
    </Suspense>
  );
}
