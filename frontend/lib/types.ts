export type SafetyTier = "routine" | "caution" | "critical";

export type Step = {
  id: number;
  title: string;
  safetyTier: SafetyTier;
  instruction: string;
  warnings?: string[];
  diagram?: string;
};

export type Procedure = {
  id: string;
  title: string;
  system: string;
  summary: string;
  steps: Step[];
};

export type Conversation = {
  id: string;
  title: string;
  procedureId: string;
  updatedAt: string;
};

export type MicPermission = "idle" | "pending" | "granted" | "denied";
