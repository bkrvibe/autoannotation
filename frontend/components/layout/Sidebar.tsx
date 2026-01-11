"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { api } from "@/lib/api";
import {
  LayoutDashboard,
  Briefcase,
  Plus,
  FolderOpen,
  HelpCircle,
  BookOpen,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Jobs", href: "/jobs", icon: Briefcase },
  { name: "Pipelines", href: "/pipelines", icon: FolderOpen },
];

const resources = [
  { name: "Documentation", href: "/docs/getting-started", icon: BookOpen, external: false },
  { name: "Support", href: "mailto:support@caliperdata.ai", icon: HelpCircle, external: true },
];

interface JobStats {
  total: number;
  completed: number;
}

export function Sidebar() {
  const pathname = usePathname();
  const [stats, setStats] = useState<JobStats>({ total: 0, completed: 0 });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const jobs = await api.jobs.list();
        setStats({
          total: jobs.length,
          completed: jobs.filter((j: { status: string }) => j.status.toLowerCase() === 'success').length
        });
      } catch {
        // Silently fail - user may not be authenticated
      }
    };
    fetchStats();
  }, [pathname]); // Refetch when route changes

  const completionPercent = stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0;

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
              item.external ? (
                <a
                  key={item.name}
                  href={item.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-[hsl(var(--sidebar-muted))] hover:text-foreground hover:bg-secondary/50 transition-all duration-150"
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </a>
              ) : (
                <Link
                  key={item.name}
                  href={item.href}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm text-[hsl(var(--sidebar-muted))] hover:text-foreground hover:bg-secondary/50 transition-all duration-150"
                >
                  <item.icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              )
            ))}
          </div>
        </div>
      </nav>

      {/* Workspace Stats */}
      <div className="p-4 mx-3 mb-3 rounded-lg bg-secondary/30 border border-border/50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-foreground">Job Completion</span>
        </div>
        <div className="mt-2 flex items-center gap-2">
          <div className="flex-1 h-1.5 rounded-full bg-border overflow-hidden">
            <div 
              className="h-full rounded-full bg-gradient-to-r from-violet-500 to-purple-500 transition-all duration-300" 
              style={{ width: `${completionPercent}%` }}
            />
          </div>
          <span className="text-[10px] text-muted-foreground">{completionPercent}%</span>
        </div>
        <p className="text-[10px] text-muted-foreground mt-1">
          {stats.completed} completed / {stats.total} total jobs
        </p>
      </div>
    </div>
  );
}
