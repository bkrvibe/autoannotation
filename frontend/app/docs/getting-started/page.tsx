'use client';

import { AppLayout } from '@/components/layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  BookOpen, 
  Play, 
  Settings, 
  CheckCircle2,
  ArrowRight,
  Folder,
  Sliders,
  Clock
} from 'lucide-react';

export default function GettingStartedPage() {
  return (
    <AppLayout title="Documentation" description="Getting started with AutoAnn">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center py-8">
          <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
            <BookOpen className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-3xl font-bold text-foreground">Getting Started with AutoAnn</h1>
          <p className="text-muted-foreground mt-2 max-w-2xl mx-auto">
            Learn how to create annotation jobs and get high-quality automated annotations for your datasets.
          </p>
        </div>

        {/* Quick Start */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Play className="h-5 w-5 text-primary" />
              Quick Start Guide
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                1
              </div>
              <div>
                <h3 className="font-medium text-foreground">Select a Pipeline</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Choose from our available pipelines based on your annotation needs:
                </p>
                <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2">
                    <ArrowRight className="h-3 w-3" />
                    <strong>2D Object Detection</strong> - Detect and classify objects in images
                  </li>
                  <li className="flex items-center gap-2">
                    <ArrowRight className="h-3 w-3" />
                    <strong>2D Instance Segmentation</strong> - Pixel-level object masks
                  </li>
                  <li className="flex items-center gap-2">
                    <ArrowRight className="h-3 w-3" />
                    <strong>2D Semantic Segmentation</strong> - Scene-level pixel classification
                  </li>
                  <li className="flex items-center gap-2">
                    <ArrowRight className="h-3 w-3" />
                    <strong>2D Object Tracking</strong> - Track objects across video frames
                  </li>
                  <li className="flex items-center gap-2">
                    <ArrowRight className="h-3 w-3" />
                    <strong>3D Object Detection & Tracking</strong> - LiDAR point cloud annotations
                  </li>
                </ul>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                2
              </div>
              <div>
                <h3 className="font-medium text-foreground flex items-center gap-2">
                  <Folder className="h-4 w-4" />
                  Provide Your Data Path
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Enter a GCS (Google Cloud Storage) path to your input data. The path should point to a folder 
                  containing your images, video frames, or point cloud data.
                </p>
                <div className="mt-2 p-3 bg-secondary/50 rounded-lg">
                  <code className="text-xs text-foreground">
                    gs://your-bucket/path/to/data/
                  </code>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                3
              </div>
              <div>
                <h3 className="font-medium text-foreground flex items-center gap-2">
                  <Sliders className="h-4 w-4" />
                  Configure Parameters (Optional)
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Adjust model parameters to fine-tune detection quality. Default values work well for most cases.
                </p>
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <div className="p-2 bg-secondary/30 rounded text-xs">
                    <span className="font-medium">Batch Size</span>
                    <p className="text-muted-foreground">Images processed at once</p>
                  </div>
                  <div className="p-2 bg-secondary/30 rounded text-xs">
                    <span className="font-medium">Box Threshold</span>
                    <p className="text-muted-foreground">Detection confidence filter</p>
                  </div>
                  <div className="p-2 bg-secondary/30 rounded text-xs">
                    <span className="font-medium">Text Threshold</span>
                    <p className="text-muted-foreground">Text detection sensitivity</p>
                  </div>
                  <div className="p-2 bg-secondary/30 rounded text-xs">
                    <span className="font-medium">NMS IoU Threshold</span>
                    <p className="text-muted-foreground">Overlapping box removal</p>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">
                4
              </div>
              <div>
                <h3 className="font-medium text-foreground flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Submit and Monitor
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Submit your job and monitor its progress. Jobs typically complete within minutes to hours 
                  depending on dataset size.
                </p>
              </div>
            </div>

            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-600 text-white flex items-center justify-center text-sm font-bold">
                <CheckCircle2 className="h-4 w-4" />
              </div>
              <div>
                <h3 className="font-medium text-foreground">Download Results</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Once complete, your annotations will be available at the specified output location in 
                  standard annotation formats (COCO, KITTI, etc.).
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tips */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-primary" />
              Tips for Best Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="p-4 border rounded-lg">
                <Badge variant="outline" className="mb-2">Data Quality</Badge>
                <p className="text-sm text-muted-foreground">
                  Use high-resolution images when possible. Avoid blurry or heavily compressed images 
                  for better detection accuracy.
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <Badge variant="outline" className="mb-2">Batch Size</Badge>
                <p className="text-sm text-muted-foreground">
                  Larger batch sizes process faster but require more memory. Start with default 
                  and adjust if needed.
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <Badge variant="outline" className="mb-2">Thresholds</Badge>
                <p className="text-sm text-muted-foreground">
                  Lower thresholds detect more objects but may include false positives. Higher 
                  thresholds are more precise but may miss some objects.
                </p>
              </div>
              <div className="p-4 border rounded-lg">
                <Badge variant="outline" className="mb-2">File Organization</Badge>
                <p className="text-sm text-muted-foreground">
                  Organize your data in a flat folder structure. The system will process all 
                  supported files in the specified path.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Support */}
        <div className="text-center py-8 border-t">
          <p className="text-sm text-muted-foreground">
            Need help? Contact us at{' '}
            <a href="mailto:support@caliperdata.ai" className="text-primary hover:underline">
              support@caliperdata.ai
            </a>
          </p>
        </div>
      </div>
    </AppLayout>
  );
}
