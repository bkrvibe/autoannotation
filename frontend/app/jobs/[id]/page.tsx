'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { api } from '@/lib/api';
import { useRequireAuth } from '@/lib/auth-context';
import { AppLayout } from '@/components/layout';
import { StatusBadge } from '@/components/common';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  ArrowLeft,
  Calendar,
  Clock,
  HardDrive,
  Download,
  Activity,
  Box,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  FileText,
  Layers,
  Loader2
} from 'lucide-react';
import { cn, formatRelativeTime } from '@/lib/utils';

export default function JobDetailPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.id as string;
  const { isAuthenticated, loading: authLoading } = useRequireAuth();
  
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      fetchJob();
    }
  }, [jobId, isAuthenticated]);

  const fetchJob = async () => {
    try {
      const data = await api.jobs.get(jobId);
      setJob(data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to load job details');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchJob();
  };

  // Show loading while checking auth
  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const response = await api.jobs.downloadArtifact(jobId);
      
      // Refresh job to get any updated artifacts
      await fetchJob();
      
      // Create download link from blob
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      
      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'annotations.json';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename=(.+)/);
        if (match) {
          filename = match[1];
        }
      }
      
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error('Download failed:', err);
      alert(err.response?.data?.detail || 'Failed to download file. The file may not exist on the worker.');
    } finally {
      setDownloading(false);
    }
  };

  if (loading) {
    return (
      <AppLayout title="Job Details">
         <div className="flex items-center justify-center h-[50vh]">
            <p className="text-muted-foreground">Loading job details...</p>
         </div>
      </AppLayout>
    );
  }

  if (error || !job) {
    return (
      <AppLayout title="Job Details">
         <div className="p-8 text-center bg-destructive/10 rounded-xl border border-destructive/20">
            <AlertCircle className="h-10 w-10 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-medium text-destructive">Error Loading Job</h3>
            <p className="text-destructive/80 mt-2">{error || 'Job not found'}</p>
            <Button variant="outline" className="mt-6" onClick={() => router.push('/jobs')}>
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Jobs
            </Button>
         </div>
      </AppLayout>
    );
  }

  const artifacts = job.result_artifacts;

  return (
    <AppLayout title={`AutoAnnJob #${job.id}`} description="View job status and results">
      <div className="max-w-6xl mx-auto space-y-4">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => router.push('/jobs')} className="pl-0 hover:pl-2 transition-all">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to AutoAnnJobs
          </Button>
          
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw className={cn("mr-2 h-3.5 w-3.5", refreshing && "animate-spin")} />
              Refresh
            </Button>
            <Button 
              size="sm"
              variant="default"
              disabled={job.status !== 'success' || downloading} 
              onClick={handleDownload}
            >
              {downloading ? (
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Download className="mr-2 h-3.5 w-3.5" />
              )}
              {downloading ? 'Downloading...' : 'Download Results'}
            </Button>
          </div>
        </div>

        {/* Status Card */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <Card className="lg:col-span-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                   <CardTitle className="text-base">Execution Status</CardTitle>
                   <CardDescription className="text-xs">Pipeline execution details</CardDescription>
                </div>
                <StatusBadge status={job.status} />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Pipeline ID</p>
                    <div className="flex items-center gap-2">
                       <Box className="h-3.5 w-3.5 text-primary" />
                       <span className="text-sm font-medium">{job.pipeline_id}</span>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">Run ID</p>
                    <div className="flex items-center gap-2">
                       <Activity className="h-3.5 w-3.5 text-muted-foreground" />
                       <span className="font-mono text-xs truncate">{job.airflow_run_id}</span>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border">
                    <div className="space-y-1">
                        <p className="text-[10px] text-muted-foreground">Created At</p>
                        <div className="flex items-center gap-1.5">
                           <Calendar className="h-3 w-3 text-muted-foreground" />
                           <span className="text-xs">{new Date(job.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-[10px] text-muted-foreground mt-0.5">{formatRelativeTime(job.created_at)}</p>
                    </div>
                    {job.updated_at && (
                        <div className="space-y-1">
                            <p className="text-[10px] text-muted-foreground">Last Updated</p>
                            <div className="flex items-center gap-1.5">
                               <Clock className="h-3 w-3 text-muted-foreground" />
                               <span className="text-xs">{new Date(job.updated_at).toLocaleString()}</span>
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
          </Card>

          {/* Config Card */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base">Configuration</CardTitle>
            </CardHeader>
            <CardContent>
               {(() => {
                 // Only show batch_size and threshold to users
                 const userFields = ['batch_size', 'box_threshold'];
                 
                 // Handle multiple config structures:
                 // 1. job.config.config.* (new nested structure)
                 // 2. job.config.* (old flat structure)
                 const nestedConfig = job.config?.config || {};
                 const flatConfig = job.config || {};
                 
                 // Collect values from both, preferring nested
                 const displayEntries: Array<[string, any]> = [];
                 
                 userFields.forEach(field => {
                   const value = nestedConfig[field] ?? flatConfig[field];
                   if (value !== undefined && value !== null) {
                     // Rename box_threshold to just threshold for display
                     const displayKey = field === 'box_threshold' ? 'threshold' : field;
                     displayEntries.push([displayKey, value]);
                   }
                 });
                 
                 if (displayEntries.length === 0) {
                   return <p className="text-sm text-muted-foreground">Using default configuration</p>;
                 }
                 
                 return (
                   <div className="space-y-2">
                     {displayEntries.map(([key, value]) => (
                       <div key={key} className="flex justify-between items-center py-1.5 border-b border-border last:border-0">
                         <span className="text-xs text-muted-foreground capitalize">
                           {key.replace(/_/g, ' ')}
                         </span>
                         <span className="text-xs font-mono text-foreground">
                           {Array.isArray(value) ? value.join(', ') : String(value)}
                         </span>
                       </div>
                     ))}
                   </div>
                 );
               })()}
            </CardContent>
          </Card>
        </div>

        {/* Result Artifacts Card - Only show for successful jobs */}
        {job.status === 'success' && artifacts && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                Annotation Results
              </CardTitle>
              <CardDescription>Output from the annotation pipeline</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                {artifacts.num_frames && (
                  <div className="p-4 rounded-lg bg-secondary/50 border border-border text-center">
                    <Layers className="h-6 w-6 text-primary mx-auto mb-2" />
                    <p className="text-2xl font-bold">{artifacts.num_frames}</p>
                    <p className="text-xs text-muted-foreground">Frames Processed</p>
                  </div>
                )}
                {artifacts.num_annotations && (
                  <div className="p-4 rounded-lg bg-secondary/50 border border-border text-center">
                    <FileText className="h-6 w-6 text-primary mx-auto mb-2" />
                    <p className="text-2xl font-bold">{artifacts.num_annotations}</p>
                    <p className="text-xs text-muted-foreground">Annotations Generated</p>
                  </div>
                )}
              </div>
              
              <div className="mt-4 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-center">
                <CheckCircle2 className="h-8 w-8 text-emerald-500 mx-auto mb-2" />
                <p className="text-sm font-medium text-foreground">Results Ready</p>
                <p className="text-xs text-muted-foreground mt-1">Click &quot;Download Results&quot; to get your annotations</p>
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* Show message when job succeeded but no artifacts found yet */}
        {job.status === 'success' && !artifacts && (
          <Card className="border-amber-500/30 bg-amber-500/5">
            <CardContent className="pt-6">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-amber-500" />
                <p className="text-sm text-muted-foreground">
                  Results not yet available. Click <strong>Download Results</strong> to fetch and download the annotation file.
                </p>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AppLayout>
  );
}
