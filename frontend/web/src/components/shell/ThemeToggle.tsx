/**
 * ThemeToggle — selector light / dark / system para el TopBar.
 * El estado vive en `useThemeStore`. Al montar, bindea el listener
 * de `prefers-color-scheme` para que el modo "system" reaccione.
 */

import { useEffect } from "react";
import { Monitor, Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { bindSystemThemeListener, useThemeStore, type Theme } from "@/lib/theme/store";

const OPTIONS: { value: Theme; label: string; icon: typeof Sun }[] = [
  { value: "light", label: "Claro", icon: Sun },
  { value: "dark", label: "Oscuro", icon: Moon },
  { value: "system", label: "Sistema", icon: Monitor },
];

export function ThemeToggle() {
  const theme = useThemeStore((s) => s.theme);
  const setTheme = useThemeStore((s) => s.setTheme);

  useEffect(() => {
    bindSystemThemeListener();
  }, []);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Cambiar tema"
          className="h-9 w-9"
        >
          <Sun className="size-4 scale-100 rotate-0 transition-all dark:scale-0 dark:-rotate-90" />
          <Moon className="absolute size-4 scale-0 rotate-90 transition-all dark:scale-100 dark:rotate-0" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        {OPTIONS.map(({ value, label, icon: Icon }) => (
          <DropdownMenuItem
            key={value}
            onClick={() => setTheme(value)}
            data-active={theme === value}
            className="cursor-pointer data-[active=true]:bg-accent-soft data-[active=true]:text-accent"
          >
            <Icon />
            {label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
