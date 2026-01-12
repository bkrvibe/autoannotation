'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { useRequireAuth } from '@/lib/auth-context';
import { AppLayout } from '@/components/layout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  Box,
  Image,
  Layers,
  Play,
  Loader2,
  AlertCircle,
  Sparkles,
  Route,
  CheckCircle2,
  Clock,
  XCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Pipeline {
  id: string;
  display_name: string;
  description: string;
  tags: string[];
}

interface Job {
  id: number;
  pipeline_id: string;
  status: string;
}

interface JobCounts {
  completed: number;
  running: number;
  failed: number;
}

// Pipeline categorization and display names
const PIPELINE_INFO: Record<string, { category: '2D' | '3D'; displayName: string; description: string }> = {
  'auto_annotation_pipeline_dynamic': {
    category: '3D',
    displayName: '3D Object Detection & Tracking',
    description: 'Automated 3D object detection and tracking for LiDAR point cloud data'
  },
  'image_auto_annotation_2d': {
    category: '2D',
    displayName: '2D Object Detection',
    description: 'Detects: vehicle, pedestrian classes'
  },
  'image_auto_annotation_2d_segmentation': {
    category: '2D',
    displayName: '2D Instance Segmentation',
    description: 'Instance segmentation for detected objects with bounding box prompts'
  },
  'image_auto_annotation_2d_semantic_segmentation': {
    category: '2D',
    displayName: '2D Semantic Segmentation',
    description: 'Segments: road, sidewalk, building, wall, fence, pole, traffic light, traffic sign, vegetation, terrain, sky, person, rider, car, truck, bus, train, motorcycle, bicycle'
  },
  'image_auto_annotation_2d_tracking': {
    category: '2D',
    displayName: '2D Object Tracking',
    description: 'Multi-object tracking with appearance features and Kalman filtering'
  }
};

function getPipelineIcon(pipelineId: string) {
  const info = PIPELINE_INFO[pipelineId];
  if (!info) return Sparkles;
  if (info.category === '3D') return Box;
  if (pipelineId.includes('segmentation')) return Layers;
  if (pipelineId.includes('tracking')) return Route;
  return Image;
}

function getPipelineDisplayInfo(pipeline: Pipeline) {
  const info = PIPELINE_INFO[pipeline.id];
  if (info) {
    return {
      displayName: info.displayName,
      description: info.description,
      category: info.category
    };
  }
  // Fallback for unknown pipelines
  return {
    displayName: pipeline.display_name,
    description: pipeline.description,
    category: pipeline.id.includes('3d') ? '3D' as const : '2D' as const
  };
}

export default function PipelinesPage() {
  const router = useRouter();
  const { isAuthenticated, loading: authLoading } = useRequireAuth();
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated) {
      fetchData();
    }
  }, [isAuthenticated]);

  const fetchData = async () => {
    try {
      const [pipelinesData, jobsData] = await Promise.all([
        api.pipelines.list(),
        api.jobs.list()
      ]);
      setPipelines(pipelinesData);
      setJobs(jobsData);
    } catch (err) {
      console.error(err);
      setError('Failed to load pipelines');
    } finally {
      setLoading(false);
    }
  };

  // Calculate job counts for a pipeline
  const getJobCounts = (pipelineId: string): JobCounts => {
    const pipelineJobs = jobs.filter(j => j.pipeline_id === pipelineId);
    return {
      completed: pipelineJobs.filter(j => j.status.toLowerCase() === 'success').length,
      running: pipelineJobs.filter(j => ['running', 'queued'].includes(j.status.toLowerCase())).length,
      failed: pipelineJobs.filter(j => j.status.toLowerCase() === 'failed').length
    };
  };

  const handleStartAnnotating = (pipelineId: string) => {
    router.push(`/jobs/new?pipeline=${pipelineId}`);
  };

  // Separate pipelines into 2D and 3D
  const pipelines3D = pipelines.filter(p => {
    const info = PIPELINE_INFO[p.id];
    return info?.category === '3D' || (!info && p.id.includes('3d'));
  });

  const pipelines2D = pipelines.filter(p => {
    const info = PIPELINE_INFO[p.id];
    return info?.category === '2D' || (!info && !p.id.includes('3d'));
  });

  if (authLoading || loading) {
    return (
      <AppLayout title="Pipelines" description="Available annotation pipelines">
        <div className="flex items-center justify-center h-[50vh]">
          <div className="flex flex-col items-center gap-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground">Loading pipelines...</p>
          </div>
        </div>
      </AppLayout>
    );
  }

  if (error) {
    return (
      <AppLayout title="Pipelines" description="Available annotation pipelines">
        <div className="p-8 text-center bg-destructive/10 rounded-xl border border-destructive/20">
          <AlertCircle className="h-10 w-10 text-destructive mx-auto mb-4" />
          <h3 className="text-lg font-medium text-destructive">Error Loading Pipelines</h3>
          <p className="text-destructive/80 mt-2">{error}</p>
        </div>
      </AppLayout>
    );
  }

  const renderPipelineCard = (pipeline: Pipeline) => {
    const Icon = getPipelineIcon(pipeline.id);
    const info = getPipelineDisplayInfo(pipeline);
    const counts = getJobCounts(pipeline.id);
    const totalJobs = counts.completed + counts.running + counts.failed;

    return (
      <Card 
        key={pipeline.id} 
        className="hover:border-primary/50 transition-colors cursor-pointer"
        onClick={() => router.push(`/jobs?pipeline=${pipeline.id}`)}
      >
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                <Icon className="h-6 w-6 text-primary" />
              </div>
              <div>
                <CardTitle className="text-lg">{info.displayName}</CardTitle>
                <Badge variant="outline" className="mt-1">
                  {info.category}
                </Badge>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground mb-4">
            {info.description}
          </p>
          
          {/* Job Statistics */}
          <div className="flex items-center gap-4 mb-4 text-sm">
            <div className="flex items-center gap-1.5 text-green-600">
              <CheckCircle2 className="h-4 w-4" />
              <span>{counts.completed}</span>
            </div>
            <div className="flex items-center gap-1.5 text-blue-600">
              <Clock className="h-4 w-4" />
              <span>{counts.running}</span>
            </div>
            <div className="flex items-center gap-1.5 text-red-600">
              <XCircle className="h-4 w-4" />
              <span>{counts.failed}</span>
            </div>
            <span className="text-muted-foreground ml-auto">
              {totalJobs} total job{totalJobs !== 1 ? 's' : ''}
            </span>
          </div>
          
          <Button 
            onClick={(e) => {
              e.stopPropagation();
              handleStartAnnotating(pipeline.id);
            }}
            className="w-full"
          >
            <Play className="mr-2 h-4 w-4" />
            Start Annotating
          </Button>
        </CardContent>
      </Card>
    );
  };

  return (
    <AppLayout title="Pipelines" description="Available annotation pipelines">
      <div className="space-y-8">
        {/* 3D Pipelines Section */}
        {pipelines3D.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-4">
              <Box className="h-6 w-6 text-primary" />
              <h2 className="text-xl font-semibold">3D Pipelines</h2>
              <Badge variant="secondary">{pipelines3D.length}</Badge>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {pipelines3D.map(renderPipelineCard)}
            </div>
          </div>
        )}

        {/* 2D Pipelines Section */}
        {pipelines2D.length > 0 && (
          <div>
            <div className="flex items-center gap-3 mb-4">
              <Image className="h-6 w-6 text-primary" />
              <h2 className="text-xl font-semibold">2D Pipelines</h2>
              <Badge variant="secondary">{pipelines2D.length}</Badge>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {pipelines2D.map(renderPipelineCard)}
            </div>
          </div>
        )}

        {pipelines.length === 0 && (
          <div className="text-center py-16">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
              <AlertCircle className="h-8 w-8 text-muted-foreground" />
            </div>
            <p className="text-lg font-medium text-foreground">No pipelines available</p>
            <p className="text-sm text-muted-foreground mt-1">
              Check Airflow connection or contact support
            </p>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
