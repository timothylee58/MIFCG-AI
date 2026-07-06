"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  ShieldCheck,
  TrendingUp,
  BarChart3,
  HeartHandshake,
  LogOut,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { createClient } from "@/lib/supabase/client";

const NAV_ITEMS = [
  {
    href: "/regcomply",
    label: "RegComply AI",
    icon: ShieldCheck,
    description: "BNM/SC compliance RAG",
    color: "text-sky-400",
  },
  {
    href: "/fxwatch",
    label: "FXWatch",
    icon: TrendingUp,
    description: "Live FX monitoring",
    color: "text-emerald-400",
  },
  {
    href: "/bursa-risk",
    label: "Bursa Risk",
    icon: BarChart3,
    description: "XGBoost factor analytics",
    color: "text-violet-400",
  },
  {
    href: "/survival-pro",
    label: "Survival Pro",
    icon: HeartHandshake,
    description: "B40 aid & spend coach",
    color: "text-amber-400",
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  return (
    <aside className="w-56 bg-sidebar flex flex-col border-r border-sidebar-border min-h-screen flex-shrink-0">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-sidebar-border">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-primary rounded-md flex items-center justify-center text-primary-foreground font-bold text-xs flex-shrink-0">
            M
          </div>
          <div>
            <div className="text-sm font-bold text-foreground leading-none">MIFCG</div>
            <div className="text-[10px] text-muted-foreground mt-0.5">Compliance Gateway</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-2 py-4 space-y-1">
        <p className="px-2 mb-2 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
          Modules
        </p>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname.startsWith(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors group",
                isActive
                  ? "bg-accent text-foreground"
                  : "text-muted-foreground hover:bg-accent/50 hover:text-foreground"
              )}
            >
              <Icon
                className={cn("w-4 h-4 flex-shrink-0", isActive ? item.color : "text-muted-foreground group-hover:" + item.color)}
                strokeWidth={isActive ? 2 : 1.5}
              />
              <div className="flex-1 min-w-0">
                <div className={cn("font-medium leading-none", isActive ? "text-foreground" : "")}>
                  {item.label}
                </div>
                <div className="text-[10px] text-muted-foreground mt-0.5 truncate">{item.description}</div>
              </div>
              {isActive && <ChevronRight className="w-3 h-3 text-primary flex-shrink-0" />}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-2 py-3 border-t border-sidebar-border">
        <button
          onClick={handleLogout}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors w-full"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  );
}
