"use client";

import { Suspense, useEffect, useState } from "react";
import Image from "next/image";
import { useSearchParams } from "next/navigation";
import LoginForm from "@/components/app-shell/LoginForm";

type Os = "mac" | "pc" | "linux";

const DOWNLOADS: Record<Os, string | null> = {
  mac: "https://github.com/BLLAKO/LMT/releases/download/v0.1.0/ZeroDelay-0.1.0-arm64.dmg",
  pc: "https://github.com/BLLAKO/LMT/releases/download/v0.1.0/ZeroDelay-Windows-0.1.0.exe",
  linux: null,
};

const OS_LABELS: Record<Os, string> = {
  mac: "macOS",
  pc: "Windows",
  linux: "Linux",
};

function getOs(value: string | null): Os {
  if (value === "pc") return "pc";
  if (value === "linux") return "linux";
  return "mac";
}

function LoginContent() {
  const searchParams = useSearchParams();
  const os = getOs(searchParams.get("os"));
  const [authenticated, setAuthenticated] = useState(false);
  const downloadHref = DOWNLOADS[os];

  useEffect(() => {
    if (authenticated && downloadHref) {
      window.location.href = downloadHref;
    }
  }, [authenticated, downloadHref]);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-page px-6">
      <Image src="/logo.png" alt="ZeroDelay" width={177} height={50} className="mb-4" />

      {!authenticated ? (
        <>
          <p className="mb-8 text-sm text-secondary">
            Sign in to download ZeroDelay for {OS_LABELS[os]}
          </p>
          <LoginForm onSuccess={() => setAuthenticated(true)} submitLabel="Sign in & download" />
        </>
      ) : downloadHref ? (
        <div className="max-w-sm text-center">
          <p className="text-sm text-secondary">
            Your download should start automatically. If it doesn&apos;t,{" "}
            <a href={downloadHref} className="font-medium text-accent-600 underline">
              click here
            </a>
            .
          </p>
        </div>
      ) : (
        <div className="max-w-sm text-center">
          <p className="text-sm text-secondary">
            You&apos;re signed in, but the {OS_LABELS[os]} build is not uploaded yet.
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