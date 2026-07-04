"use client";

import { useState } from "react";

export default function LoginForm({
  onSuccess,
  submitLabel = "Continue",
}: {
  onSuccess: (company: string) => void;
  submitLabel?: string;
}) {
  const [company, setCompany] = useState("");
  const [accessCode, setAccessCode] = useState("");
  const [error, setError] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!company.trim() || !accessCode.trim()) {
      setError("Enter your company name and access code.");
      return;
    }
    // TODO: real auth — this just checks both fields are filled in. Replace
    // with a real call that verifies the company + access code issued to
    // the technician's organization once a backend exists.
    window.localStorage.setItem("zerodelay:company", company.trim());
    window.localStorage.setItem("zerodelay:authenticated", "true");
    onSuccess(company.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-sm">
      <label htmlFor="company" className="mb-2 block text-sm font-medium text-secondary">
        Company name
      </label>
      <input
        id="company"
        type="text"
        value={company}
        onChange={(e) => {
          setCompany(e.target.value);
          setError("");
        }}
        placeholder="Acme Orbital Services"
        autoFocus
        className="mb-4 w-full rounded-xl border border-border bg-sunken px-4 py-3 text-sm outline-none placeholder:text-muted focus:border-accent-500"
      />

      <label htmlFor="accessCode" className="mb-2 block text-sm font-medium text-secondary">
        Access code
      </label>
      <input
        id="accessCode"
        type="password"
        value={accessCode}
        onChange={(e) => {
          setAccessCode(e.target.value);
          setError("");
        }}
        placeholder="Provided by your organization"
        className="w-full rounded-xl border border-border bg-sunken px-4 py-3 text-sm outline-none placeholder:text-muted focus:border-accent-500"
      />

      {error && <p className="mt-2 text-sm text-danger">{error}</p>}
      <button
        type="submit"
        className="mt-4 w-full rounded-xl bg-accent-500 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-accent-600"
      >
        {submitLabel}
      </button>
    </form>
  );
}
