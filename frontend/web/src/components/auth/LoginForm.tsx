/**
 * Iter 1 — Login.
 * Card centrada con form (RHF + Zod) → POST /auth/login → Zustand store + redirect.
 *
 * En dev (localhost / 127.0.0.1) muestra el campo "subdominio".
 * En producción (subdominio real en el host), el campo se oculta y el backend
 * resuelve el tenant del header Host.
 */

import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, Loader2, LogIn } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import * as z from "zod";

import { AppProviders } from "@/components/AppProviders";
import { MukusoftMark, TenantLogo } from "@/components/branding/Logos";
import { getDefaultRouteForPermissions } from "@/components/shell/nav-config";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { ApiError } from "@/lib/api/client";
import { useLogin } from "@/lib/api/queries/auth";
import { useBrandStore } from "@/lib/branding/store";
import { cn } from "@/lib/utils";
import { IS_DEMO, withBase } from "@/lib/paths";

const DEV_HOSTS = new Set(["localhost", "127.0.0.1", ""]);
const DEFAULT_SUBDOMAIN = "demo";

const loginSchema = z.object({
  username: z.string().min(1, "Ingresá tu usuario"),
  password: z.string().min(1, "Ingresá tu contraseña"),
  subdominio: z.string().optional(),
});

type LoginFormValues = z.infer<typeof loginSchema>;

function isDevHost() {
  if (typeof window === "undefined") return true;
  return DEV_HOSTS.has(window.location.hostname);
}

function LoginFormInner() {
  const [showSubdomain, setShowSubdomain] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const login = useLogin();
  const brand = useBrandStore((s) => s.brand);

  useEffect(() => {
    setShowSubdomain(isDevHost());
  }, []);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: IS_DEMO ? "admin" : "",
      password: IS_DEMO ? "demo" : "",
      subdominio: DEFAULT_SUBDOMAIN,
    },
  });

  const onSubmit = (values: LoginFormValues) => {
    const payload = {
      username: values.username.trim(),
      password: values.password,
      subdominio: showSubdomain ? values.subdominio?.trim() || undefined : undefined,
    };

    login.mutate(payload, {
      onSuccess: (data) => {
        toast.success("¡Bienvenido!", { description: "Sesión iniciada correctamente." });
        // Redirect a la primera ruta permitida (ej. operario sin dashboard
        // va directo a /sales/new).
        window.location.href = withBase(getDefaultRouteForPermissions(data.permissions));
      },
      onError: (err) => {
        const message = err instanceof ApiError
          ? err.message
          : "No se pudo iniciar sesión.";
        toast.error("Error al iniciar sesión", { description: message });
      },
    });
  };

  const isSubmitting = login.isPending;

  return (
    <div className="flex w-full max-w-md flex-col items-center gap-6">
      {/* Logo del tenant (fallback Carwash) — arriba, grande */}
      <div className="flex flex-col items-center gap-3 animate-fade-in-up">
        <TenantLogo className="h-20 w-auto sm:h-24" alt="Logo" />
        {!brand.logoUrl ? (
          <p className="text-xl font-semibold tracking-tight text-text-primary">
            <span className="text-brand-sky">C</span>
            <span className="text-brand-deep">arwash</span>
          </p>
        ) : null}
      </div>

      <article
        className={cn(
          "animate-fade-in-up w-full overflow-hidden rounded-2xl",
          // Vidrio con sombra de panel flotante: es la única pieza de la pantalla.
          "border border-white/60 bg-bg-surface shadow-elevated dark:border-white/10",
        )}
      >
        <div className="p-6 sm:p-8">
        <div className="mb-6 space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Iniciar sesión</h1>
          <p className="text-sm text-text-secondary">
            Accedé con tu usuario de la lavandería.
          </p>
        </div>

        {IS_DEMO ? (
          <p className="mb-5 rounded-md border border-accent/25 bg-accent-soft px-3 py-2.5 text-[13px] leading-relaxed text-text-secondary">
            Demo con datos de ejemplo. Entrá como{" "}
            <span className="font-medium text-text-primary">admin</span> o como{" "}
            <span className="font-medium text-text-primary">cajero</span> (con menos
            permisos). La contraseña puede ser cualquiera.
          </p>
        ) : null}

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="username"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Usuario</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="username"
                      autoFocus
                      placeholder="admin"
                      disabled={isSubmitting}
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="password"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contraseña</FormLabel>
                  <FormControl>
                    <div className="relative">
                      <Input
                        type={showPassword ? "text" : "password"}
                        autoComplete="current-password"
                        placeholder="••••••••"
                        disabled={isSubmitting}
                        className="pr-10"
                        {...field}
                      />
                      <button
                        type="button"
                        onClick={() => setShowPassword((v) => !v)}
                        disabled={isSubmitting}
                        aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                        aria-pressed={showPassword}
                        className="absolute right-2 top-1/2 -translate-y-1/2 grid h-7 w-7 place-items-center rounded-md text-text-tertiary hover:bg-bg-sunken hover:text-text-primary disabled:opacity-40"
                      >
                        {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                      </button>
                    </div>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {showSubdomain && (
              <FormField
                control={form.control}
                name="subdominio"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Subdominio</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="demo"
                        disabled={isSubmitting}
                        {...field}
                      />
                    </FormControl>
                    <p className="text-xs text-text-tertiary">
                      Identifica la lavandería. En producción se detecta del host.
                    </p>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            <Button
              type="submit"
              className="h-10 w-full bg-accent font-medium text-white hover:bg-accent-hover dark:text-bg-app"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="animate-spin" />
                  Ingresando…
                </>
              ) : (
                <>
                  <LogIn />
                  Ingresar
                </>
              )}
            </Button>
          </form>
        </Form>

        </div>
      </article>

      {/* Powered by Mukusoft — sólo si el tenant lo permite */}
      {brand.showMukusoft ? (
        <div className="flex flex-col items-center gap-1.5 opacity-80">
          <p className="text-[11px] text-text-tertiary">
            Powered by
          </p>
          <MukusoftMark className="h-9 w-auto sm:h-10" />
        </div>
      ) : null}
    </div>
  );
}

export function LoginForm() {
  return (
    <AppProviders>
      <LoginFormInner />
    </AppProviders>
  );
}
