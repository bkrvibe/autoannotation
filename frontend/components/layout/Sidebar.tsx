"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Briefcase,
  Plus,
  FolderOpen,
  HelpCircle,
  BookOpen,
  ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Jobs", href: "/jobs", icon: Briefcase },
  { name: "Pipelines", href: "/pipelines", icon: FolderOpen },
];

const resources = [
  { name: "Documentation", href: "#", icon: BookOpen, external: true },
  { name: "API Reference", href: "#", icon: ExternalLink, external: true },
  { name: "Support", href: "#", icon: HelpCircle, external: true },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex flex-col h-full w-60 bg-[hsl(var(--sidebar))] border-r border-[hsl(var(--sidebar-border))]">
      {/* Logo */}
      <div className="flex items-center h-16 px-5 border-b border-[hsl(var(--sidebar-border))]">
        <Link href="/dashboard" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <span className="text-white font-bold text-sm">C</span>
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-sm text-foreground">CaliperAI</span>
            <span className="text-[10px] text-[hsl(var(--sidebar-muted))] uppercase tracking-wider">AutoAnn</span>
          </div>
        </Link>
      </div>

      {/* New Job Button */}
      <div className="px-4 py-4">
        <Link href="/jobs/new">
          <Button className="w-full justify-start gap-2 bg-primary hover:bg-primary/90 shadow-lg shadow-primary/20">
            <Plus className="h-4 w-4" />
            New Annotation Job
          </Button>
        </Link>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 px-3">
        <div className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150",
                  isActive
                    ? "bg-primary/10 text-primary border-l-2 border-primary ml-[-1px]"
                    : "text-[hsl(var(--sidebar-muted))] hover:text-foreground hover:bg-secondary/50"
                )}
              >
                <item.icon className={cn("h-[18px] w-[18px]", isActive && "text-primary")} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </div>

        {/* Resources Section */}
        <div className="mt-8">
          <h4 className="px-3 text-[11px] font-medium uppercase tracking-wider text-[hsl(var(--sidebar-muted))] mb-2">
            Resources
          </h4>
          <div className="space-y-1">
            {resources.map((item) => (
              <a
                key={item.name}
                href={item.href}
                target={item.external ? "_blank" : undefined}
                rel={item.external ? "noopener noreferrer" : undefined}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-[hsl(var(--sidebar-muted))] hover:text-foreground hover:bg-secondary/50 transition-all duration-150"
              >
                <item.icon className="h-4 w-4" />
                <span>{item.name}</span>
                {item.external && <ExternalLink className="h-3 w-3 ml-auto opacity-50" />}
              </a>
            ))}
          </div>
        </div>
      </nav>

      {/* Workspace Info */}
      <div className="p-4 mx-3 mb-3 rounded-lg bg-secondary/30 border border-border/50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-foreground">Workspace</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/20 text-primary font-medium">
            Enterprise
          </span>
        </div>
        <p className="text-xs text-muted-foreground">Caliper AI</p>
        <div className="mt-2 flex items-center gap-2">
          <div className="flex-1 h-1.5 rounded-full bg-border overflow-hidden">
            <div className="h-full w-[65%] rounded-full bg-gradient-to-r from-violet-500 to-purple-500" />
          </div>
          <span className="text-[10px] text-muted-foreground">65%</span>
        </div>
        <p className="text-[10px] text-muted-foreground mt-1">847 / 1,000 jobs</p>
      </div>
    </div>
  );
}
