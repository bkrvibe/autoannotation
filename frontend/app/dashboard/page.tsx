'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { api } from '@/lib/api';
import { useAuth, useRequireAuth } from '@/lib/auth-context';
import { AppLayout } from '@/components/layout';
import { StatusBadge } from '@/components/common';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  Briefcase, 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  Clock,
  ArrowRight,
  TrendingUp,
  Activity,
  Plus,
  Play
} from 'lucide-react';
import { formatRelativeTime, cn } from '@/lib/utils';

interface Job {
  id: number;
  pipeline_id: string;
  input_uri: string;
  status: string;
  created_at: string;
  airflow_run_id: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useRequireAuth();
  const { user, tenant } = useAuth();
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchJobs();
    }
  }, [isAuthenticated]);

  // Auto-refresh job status every 5 seconds
  useEffect(() => {
    if (!isAuthenticated) return;

    const interval = setInterval(() => {
      fetchJobs();
    }, 5000);

    return () => clearInterval(interval);
  }, [isAuthenticated]);

  const fetchJobs = async () => {
    try {
      const data = await api.jobs.list();
      setJobs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  // Calculate stats
  const totalJobs = jobs.length;
  const runningJobs = jobs.filter(j => j.status.toLowerCase() === 'running' || j.status.toLowerCase() === 'queued').length;
  const successfulJobs = jobs.filter(j => j.status.toLowerCase() === 'success').length;
  const failedJobs = jobs.filter(j => j.status.toLowerCase() === 'failed').length;
  const successRate = totalJobs > 0 ? Math.round((successfulJobs / totalJobs) * 100) : 0;
  
  const activeJobs = jobs.filter(j => 
    j.status.toLowerCase() === 'running' || j.status.toLowerCase() === 'queued'
  ).slice(0, 3);
  
  const recentCompleted = jobs.filter(j => 
    j.status.toLowerCase() === 'success' || j.status.toLowerCase() === 'failed'
  ).slice(0, 5);

  const stats = [
    {
      label: 'Total AutoAnnJobs',
      value: totalJobs,
      subtext: 'All time',
      icon: Briefcase,
      color: 'text-violet-400',
      bgColor: 'bg-violet-500/10',
      href: '/jobs',
    },
    {
      label: 'Running',
      value: runningJobs,
      subtext: 'In progress',
      icon: Activity,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
      pulse: runningJobs > 0,
      href: '/jobs?status=running',
    },
    {
      label: 'Completed',
      value: successfulJobs,
      subtext: `${successRate}% success rate`,
      icon: CheckCircle2,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10',
      href: '/jobs?status=success',
    },
    {
      label: 'Failed',
      value: failedJobs,
      subtext: 'Need attention',
      icon: XCircle,
      color: 'text-red-400',
      bgColor: 'bg-red-500/10',
      href: '/jobs?status=failed',
    },
  ];

  if (loading) {
    return (
      <AppLayout title="Dashboard">
        <div className="flex items-center justify-center h-[60vh]">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading dashboard...</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout title="Dashboard" description="Monitor your AutoAnnJobs">
      <div className="space-y-8">
        {/* Welcome Banner */}
        <div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-violet-600/20 via-purple-600/20 to-fuchsia-600/20 border border-violet-500/20 p-6">
          <div className="absolute inset-0 bg-grid-white/[0.02]" />
          <div className="relative flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                Welcome back, Admin
              </h2>
              <p className="mt-1 text-muted-foreground">
                {runningJobs > 0 
                  ? `You have ${runningJobs} AutoAnnJob${runningJobs > 1 ? 's' : ''} currently running.`
                  : 'Start a new AutoAnnJob to begin processing your data.'
                }
              </p>
            </div>
            <Link href="/jobs/new">
              <Button className="shadow-lg shadow-primary/20">
                <Plus className="mr-2 h-4 w-4" />
                New AutoAnnJob
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat) => (
            <Link key={stat.label} href={stat.href}>
              <Card className="relative overflow-hidden transition-all hover:shadow-md hover:border-primary/30 cursor-pointer">
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground">{stat.label}</p>
                      <p className="mt-2 text-3xl font-semibold text-foreground">{stat.value}</p>
                      <p className="mt-1 text-xs text-muted-foreground">{stat.subtext}</p>
                    </div>
                    <div className={cn("p-2.5 rounded-lg", stat.bgColor)}>
                      <stat.icon className={cn("h-5 w-5", stat.color, stat.pulse && "animate-pulse")} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-5">
          {/* Active Jobs - Takes more space */}
          <div className="lg:col-span-3">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-4">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-4 w-4 text-blue-400" />
                    Active Jobs
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">Currently processing</p>
                </div>
                <Link href="/jobs?status=running">
                  <Button variant="ghost" size="sm" className="text-muted-foreground">
                    View all
                    <ArrowRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent>
                {activeJobs.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <div className="w-12 h-12 rounded-full bg-muted flex items-center justify-center mb-4">
                      <Clock className="h-6 w-6 text-muted-foreground" />
                    </div>
                    <p className="text-muted-foreground">No active jobs</p>
                    <p className="text-sm text-muted-foreground/60 mt-1">Start a new job to see it here</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {activeJobs.map((job) => (
                      <div
                        key={job.id}
                        onClick={() => router.push(`/jobs/${job.id}`)}
                        className="group p-4 rounded-lg border border-border/50 bg-secondary/30 hover:bg-secondary/50 hover:border-border transition-all cursor-pointer"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <StatusBadge status={job.status} />
                            <span className="text-sm font-medium text-foreground">
                              {job.pipeline_id}
                            </span>
                          </div>
                          <span className="text-xs text-muted-foreground">
                            {formatRelativeTime(job.created_at)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <code className="text-xs text-muted-foreground font-mono truncate max-w-[300px]">
                            {job.input_uri}
                          </code>
                        </div>
                        {/* Simulated progress bar */}
                        <div className="mt-3 h-1.5 rounded-full bg-border overflow-hidden">
                          <div 
                            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-violet-500 transition-all duration-1000"
                            style={{ width: job.status.toLowerCase() === 'running' ? '65%' : '20%' }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Completed */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-4">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-emerald-400" />
                    Recent
                  </CardTitle>
                  <p className="text-sm text-muted-foreground mt-1">Latest completed</p>
                </div>
                <Link href="/jobs">
                  <Button variant="ghost" size="sm" className="text-muted-foreground">
                    View all
                    <ArrowRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </Link>
              </CardHeader>
              <CardContent>
                {recentCompleted.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-8 text-center">
                    <p className="text-sm text-muted-foreground">No completed jobs yet</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {recentCompleted.map((job) => (
                      <div
                        key={job.id}
                        onClick={() => router.push(`/jobs/${job.id}`)}
                        className="flex items-center justify-between p-3 rounded-lg hover:bg-secondary/50 transition-colors cursor-pointer group"
                      >
                        <div className="flex items-center gap-3 min-w-0">
                          <div className={cn(
                            "w-2 h-2 rounded-full flex-shrink-0",
                            job.status.toLowerCase() === 'success' ? 'bg-emerald-400' : 'bg-red-400'
                          )} />
                          <span className="text-sm font-medium truncate">
                            {job.pipeline_id}
                          </span>
                        </div>
                        <span className="text-xs text-muted-foreground flex-shrink-0 ml-2">
                          {formatRelativeTime(job.created_at)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
