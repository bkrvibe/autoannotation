'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { useRequireAuth } from '@/lib/auth-context';
import { AppLayout } from '@/components/layout';
import { StatusBadge } from '@/components/common';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { 
  Search, 
  Loader2,
  Filter,
  ArrowUpDown,
  Download,
  Eye,
  X
} from 'lucide-react';
import { formatRelativeTime, cn } from '@/lib/utils';

interface Job {
  id: number;
  pipeline_id: string;
  input_uri: string;
  status: string;
  created_at: string;
  airflow_run_id: string;
  result_artifacts?: {
    output_uri?: string;
  };
}

const statusFilters = [
  { key: null, label: 'All Jobs' },
  { key: 'running', label: 'Running' },
  { key: 'queued', label: 'Queued' },
  { key: 'success', label: 'Completed' },
  { key: 'failed', label: 'Failed' },
];

export default function JobsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { isAuthenticated, loading: authLoading } = useRequireAuth();
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [pipelineFilter, setPipelineFilter] = useState<string | null>(null);

  // Read pipeline filter from URL
  useEffect(() => {
    const pipeline = searchParams.get('pipeline');
    if (pipeline) {
      setPipelineFilter(pipeline);
    }
  }, [searchParams]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchJobs();
    }
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

  // Filter jobs
  const filteredJobs = jobs.filter(job => {
    const matchesSearch = 
      job.pipeline_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.input_uri.toLowerCase().includes(searchQuery.toLowerCase()) ||
      job.id.toString().includes(searchQuery);
    
    let matchesStatus = true;
    if (statusFilter) {
      if (statusFilter === 'running') {
        matchesStatus = job.status.toLowerCase() === 'running' || job.status.toLowerCase() === 'queued';
      } else {
        matchesStatus = job.status.toLowerCase() === statusFilter;
      }
    }

    const matchesPipeline = !pipelineFilter || job.pipeline_id === pipelineFilter;
    
    return matchesSearch && matchesStatus && matchesPipeline;
  });

  const clearPipelineFilter = () => {
    setPipelineFilter(null);
    router.push('/jobs');
  };

  if (loading) {
    return (
      <AppLayout title="Jobs" description="Manage annotation jobs">
        <div className="flex items-center justify-center h-[60vh]">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading jobs...</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout title="Jobs" description="Manage annotation jobs">
      <div className="space-y-6">
        {/* Pipeline Filter Banner */}
        {pipelineFilter && (
          <div className="flex items-center gap-2 p-3 bg-primary/10 rounded-lg border border-primary/20">
            <span className="text-sm text-foreground">
              Showing jobs for: <span className="font-medium">{pipelineFilter}</span>
            </span>
            <Button 
              variant="ghost" 
              size="icon-sm" 
              onClick={clearPipelineFilter}
              className="ml-auto"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )}

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
          <div className="flex items-center gap-3 w-full sm:w-auto">
            {/* Search */}
            <div className="relative flex-1 sm:w-80">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by pipeline, ID, or path..."
                className="pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            
            <Button variant="outline" size="icon" className="flex-shrink-0">
              <Filter className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">
              {filteredJobs.length} job{filteredJobs.length !== 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Status Tabs */}
        <div className="flex gap-1 p-1 bg-secondary/50 rounded-lg w-fit">
          {statusFilters.map((filter) => (
            <button
              key={filter.key ?? 'all'}
              onClick={() => setStatusFilter(filter.key)}
              className={cn(
                "px-4 py-2 text-sm font-medium rounded-md transition-all",
                statusFilter === filter.key
                  ? "bg-background text-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {filter.label}
            </button>
          ))}
        </div>

        {/* Jobs Table */}
        <Card className="overflow-hidden">
          <CardContent className="p-0">
            {filteredJobs.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                  <Search className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-medium text-foreground">No jobs found</h3>
                <p className="text-sm text-muted-foreground mt-1 max-w-sm">
                  {searchQuery || statusFilter 
                    ? "Try adjusting your search or filters" 
                    : "Get started by creating your first annotation job"}
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border/50">
                      <th className="h-11 px-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        <button className="flex items-center gap-1 hover:text-foreground transition-colors">
                          Status
                        </button>
                      </th>
                      <th className="h-11 px-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        <button className="flex items-center gap-1 hover:text-foreground transition-colors">
                          Job ID
                          <ArrowUpDown className="h-3 w-3" />
                        </button>
                      </th>
                      <th className="h-11 px-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Pipeline
                      </th>
                      <th className="h-11 px-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Input Path
                      </th>
                      <th className="h-11 px-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        <button className="flex items-center gap-1 hover:text-foreground transition-colors">
                          Created
                          <ArrowUpDown className="h-3 w-3" />
                        </button>
                      </th>
                      <th className="h-11 px-4 text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50">
                    {filteredJobs.map((job) => (
                      <tr 
                        key={job.id} 
                        className="group transition-colors hover:bg-secondary/30 cursor-pointer"
                        onClick={() => router.push(`/jobs/${job.id}`)}
                      >
                        <td className="px-4 py-4">
                          <StatusBadge status={job.status} />
                        </td>
                        <td className="px-4 py-4">
                          <span className="font-mono text-sm text-foreground">
                            #{job.id}
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-foreground truncate max-w-[200px]">
                              {job.pipeline_id}
                            </span>
                          </div>
                        </td>
                        <td className="px-4 py-4">
                          <code className="text-xs text-muted-foreground font-mono truncate max-w-[250px] block">
                            {job.input_uri}
                          </code>
                        </td>
                        <td className="px-4 py-4">
                          <span className="text-sm text-muted-foreground">
                            {formatRelativeTime(job.created_at)}
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button 
                              variant="ghost" 
                              size="icon-sm"
                              title="View Details"
                              onClick={(e) => {
                                e.stopPropagation();
                                router.push(`/jobs/${job.id}`);
                              }}
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            {job.result_artifacts?.output_uri && (
                              <Button 
                                variant="ghost" 
                                size="icon-sm"
                                title="Copy Output Path"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  navigator.clipboard.writeText(job.result_artifacts!.output_uri!);
                                }}
                              >
                                <Download className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}
