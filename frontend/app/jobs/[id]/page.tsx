'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { api } from '@/lib/api';
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
  
  const [job, setJob] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
    } else {
      fetchJob();
    }
  }, [jobId]);

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
    <AppLayout title={`Job #${job.id}`} description="View job status and results">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => router.push('/jobs')} className="pl-0 hover:pl-2 transition-all">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Jobs
          </Button>
          
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw className={cn("mr-2 h-4 w-4", refreshing && "animate-spin")} />
              Refresh
            </Button>
            <Button 
              variant="default"
              disabled={job.status !== 'success' || downloading} 
              onClick={handleDownload}
            >
              {downloading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Download className="mr-2 h-4 w-4" />
              )}
              {downloading ? 'Downloading...' : 'Download Results'}
            </Button>
          </div>
        </div>

        {/* Status Card */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="md:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                   <CardTitle className="text-lg">Execution Status</CardTitle>
                   <CardDescription>Pipeline execution details</CardDescription>
                </div>
                <StatusBadge status={job.status} />
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">Pipeline ID</p>
                    <div className="flex items-center gap-2">
                       <Box className="h-4 w-4 text-primary" />
                       <span className="font-medium">{job.pipeline_id}</span>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider">Run ID</p>
                    <div className="flex items-center gap-2">
                       <Activity className="h-4 w-4 text-muted-foreground" />
                       <span className="font-mono text-sm">{job.airflow_run_id}</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-lg bg-secondary/50 border border-border">
                  <div className="space-y-1">
                    <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Input Source</p>
                    <div className="flex items-center gap-2 overflow-hidden">
                       <HardDrive className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                       <code className="text-sm flex-1 truncate">{job.input_uri}</code>
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
                    <div className="space-y-1">
                        <p className="text-xs text-muted-foreground">Created At</p>
                        <div className="flex items-center gap-2">
                           <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
                           <span className="text-sm">{new Date(job.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{formatRelativeTime(job.created_at)}</p>
                    </div>
                    {job.updated_at && (
                        <div className="space-y-1">
                            <p className="text-xs text-muted-foreground">Last Updated</p>
                            <div className="flex items-center gap-2">
                               <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                               <span className="text-sm">{new Date(job.updated_at).toLocaleString()}</span>
                            </div>
                        </div>
                    )}
                </div>
            </CardContent>
          </Card>

          {/* Config Card */}
          <Card className="h-fit">
            <CardHeader>
              <CardTitle className="text-lg">Configuration</CardTitle>
            </CardHeader>
            <CardContent>
               <pre className="text-xs font-mono bg-[#0c0e14] p-4 rounded-lg overflow-auto max-h-[300px] border border-border">
                  {JSON.stringify(job.config, null, 2)}
               </pre>
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
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {artifacts.num_frames && (
                  <div className="p-4 rounded-lg bg-secondary/50 border border-border text-center">
                    <Layers className="h-6 w-6 text-primary mx-auto mb-2" />
                    <p className="text-2xl font-bold">{artifacts.num_frames}</p>
                    <p className="text-xs text-muted-foreground">Frames</p>
                  </div>
                )}
                {artifacts.num_annotations && (
                  <div className="p-4 rounded-lg bg-secondary/50 border border-border text-center">
                    <FileText className="h-6 w-6 text-primary mx-auto mb-2" />
                    <p className="text-2xl font-bold">{artifacts.num_annotations}</p>
                    <p className="text-xs text-muted-foreground">Annotations</p>
                  </div>
                )}
              </div>
              
              {artifacts.calipergt_file && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">Output File</p>
                  <code className="block p-3 rounded-lg bg-[#0c0e14] text-sm font-mono border border-border break-all">
                    {artifacts.calipergt_file}
                  </code>
                </div>
              )}
              
              {artifacts.calipergt_output_dir && (
                <div className="space-y-2 mt-4">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">Output Directory</p>
                  <code className="block p-3 rounded-lg bg-[#0c0e14] text-sm font-mono border border-border break-all">
                    {artifacts.calipergt_output_dir}
                  </code>
                </div>
              )}

              {/* Show raw artifacts if they exist but don't match expected structure */}
              {!artifacts.calipergt_file && !artifacts.num_frames && (
                <div className="space-y-2">
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">Raw Artifacts</p>
                  <pre className="text-xs font-mono bg-[#0c0e14] p-4 rounded-lg overflow-auto max-h-[200px] border border-border">
                    {JSON.stringify(artifacts, null, 2)}
                  </pre>
                </div>
              )}
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
