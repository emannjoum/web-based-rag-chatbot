import { useState } from "react";
import { Loader2 } from "lucide-react";

interface AuthModalProps {
  error: string | null;
  onLogin: (email: string, password: string) => Promise<void>;
  onRegister: (email: string, password: string, displayName: string) => Promise<void>;
  onClearError: () => void;
}

export default function AuthModal({ error, onLogin, onRegister, onClearError }: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const switchMode = (nextMode: "login" | "register") => {
    setMode(nextMode);
    onClearError();
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      if (mode === "login") {
        await onLogin(email, password);
      } else {
        await onRegister(email, password, displayName);
      }
    } catch {
      // Error state is handled by useAuth.
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-border-subtle bg-surface-base p-6 shadow-2xl">
        <div className="mb-6 text-center">
          <h2 className="text-xl font-semibold text-text-primary" style={{ fontFamily: "var(--font-serif)" }}>
            MedAtlas
          </h2>
          <p className="mt-1 text-sm text-text-muted">
            {mode === "login" ? "Sign in to access your consultations" : "Create your MedAtlas account"}
          </p>
        </div>

        <div className="mb-5 flex rounded-lg bg-surface-muted p-1">
          <button
            type="button"
            onClick={() => switchMode("login")}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              mode === "login"
                ? "bg-surface-base text-text-primary shadow-sm"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            Sign in
          </button>
          <button
            type="button"
            onClick={() => switchMode("register")}
            className={`flex-1 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              mode === "register"
                ? "bg-surface-base text-text-primary shadow-sm"
                : "text-text-muted hover:text-text-secondary"
            }`}
          >
            Register
          </button>
        </div>

        <form onSubmit={(event) => void handleSubmit(event)} className="space-y-4">
          {mode === "register" && (
            <div>
              <label htmlFor="displayName" className="mb-1.5 block text-xs font-medium text-text-muted">
                Display name
              </label>
              <input
                id="displayName"
                type="text"
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                required
                className="w-full rounded-lg border border-border-subtle bg-surface-muted px-3 py-2.5 text-sm text-text-primary outline-none transition-colors focus:border-accent/50"
                placeholder="Dr. Smith"
              />
            </div>
          )}

          <div>
            <label htmlFor="email" className="mb-1.5 block text-xs font-medium text-text-muted">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              autoComplete="email"
              className="w-full rounded-lg border border-border-subtle bg-surface-muted px-3 py-2.5 text-sm text-text-primary outline-none transition-colors focus:border-accent/50"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1.5 block text-xs font-medium text-text-muted">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              minLength={8}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              className="w-full rounded-lg border border-border-subtle bg-surface-muted px-3 py-2.5 text-sm text-text-primary outline-none transition-colors focus:border-accent/50"
              placeholder="At least 8 characters"
            />
          </div>

          {error && (
            <p className="rounded-lg border border-red-400/30 bg-red-400/10 px-3 py-2 text-sm text-red-300">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-accent/90 disabled:opacity-60"
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}
