'use client';

import { Suspense, useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { api } from '@/lib/api';
import { useRequireAuth } from '@/lib/auth-context';
import { AppLayout } from '@/components/layout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { 
  ArrowLeft, 
  ArrowRight, 
  Check, 
  Loader2,
  FolderInput,
  Settings,
  Play,
  Sparkles,
  Box,
  Image,
  Layers,
  CheckCircle2,
  AlertCircle,
  Route
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Progress } from "@/components/ui/progress"


interface Pipeline {
  id: string;
  display_name: string;
  description: string;
  tags: string[];
  conf_schema: any;
  conf_defaults: any;
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
    description: 'Multi-class object detection using GroundingDINO with CLIP classification'
  },
  'image_auto_annotation_2d_segmentation': {
    category: '2D',
    displayName: '2D Instance Segmentation',
    description: 'Instance segmentation using SAM2 with bounding box prompts'
  },
  'image_auto_annotation_2d_semantic_segmentation': {
    category: '2D',
    displayName: '2D Semantic Segmentation',
    description: 'Semantic segmentation using Mask2Former/OneFormer on Cityscapes classes'
  },
  'image_auto_annotation_2d_tracking': {
    category: '2D',
    displayName: '2D Object Tracking',
    description: 'Multi-object tracking with appearance features and Kalman filtering'
  }
};

function getPipelineDisplayInfo(pipeline: Pipeline) {
  const info = PIPELINE_INFO[pipeline.id];
  if (info) {
    return {
      displayName: info.displayName,
      description: info.description,
      category: info.category
    };
  }
  return {
    displayName: pipeline.display_name,
    description: pipeline.description,
    category: pipeline.id.includes('3d') ? '3D' as const : '2D' as const
  };
}

// Separate component for number input to handle local state properly
function ConfigNumberInput({ 
  label, 
  value, 
  onChange, 
  isBatchSize, 
  isThreshold 
}: { 
  label: string; 
  value: number; 
  onChange: (val: number) => void; 
  isBatchSize: boolean; 
  isThreshold: boolean; 
}) {
  const [localValue, setLocalValue] = useState<string>(String(value));
  
  // Sync local value when external value changes
  useEffect(() => {
    setLocalValue(String(value));
  }, [value]);
  
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawValue = e.target.value;
    setLocalValue(rawValue); // Allow any input including empty
  };
  
  const handleBlur = () => {
    // On blur, parse and update the actual config
    if (localValue === '' || isNaN(Number(localValue))) {
      // Reset to current value if empty or invalid
      setLocalValue(String(value));
    } else {
      const parsed = isBatchSize 
        ? Math.max(1, parseInt(localValue) || 1)
        : Math.max(0, Math.min(isThreshold ? 1 : Infinity, parseFloat(localValue) || 0));
      setLocalValue(String(parsed));
      onChange(parsed);
    }
  };
  
  return (
    <div className="p-4 rounded-lg border border-border bg-card">
      <label className="text-sm font-medium text-foreground block mb-2">
        {label}
      </label>
      <div className="flex items-center gap-3">
        <Input
          type="text"
          inputMode={isBatchSize ? "numeric" : "decimal"}
          value={localValue}
          onChange={handleChange}
          onBlur={handleBlur}
          className="w-28 font-mono"
        />
        <span className="text-xs text-muted-foreground flex-1">
          {isBatchSize ? 'Images per batch' : isThreshold ? '0.0 - 1.0' : ''}
        </span>
      </div>
    </div>
  );
}

const steps = [
  { id: 1, name: 'Model', description: 'Choose annotation model' },
  { id: 2, name: 'Data', description: 'Input source' },
  { id: 3, name: 'Config', description: 'Parameters' },
  { id: 4, name: 'Launch', description: 'Review & run' },
];

function getPipelineIcon(pipeline: Pipeline) {
  const id = pipeline.id.toLowerCase();
  if (id.includes('auto_annotation_pipeline_dynamic')) return Box;
  if (id.includes('tracking')) return Route;
  if (id.includes('segmentation')) return Layers;
  if (id.includes('2d') || id.includes('image')) return Image;
  return Sparkles;
}

function NewJobContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const preselectedPipelineId = searchParams.get('pipeline');
  const { isAuthenticated, loading: authLoading } = useRequireAuth();
  
  const [step, setStep] = useState(1);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  
  // Form State
  const [inputUri, setInputUri] = useState('');
  const [config, setConfig] = useState<any>({});
  const [defaultConfig, setDefaultConfig] = useState<any>({}); // Track defaults to compare
  const [userModifiedKeys, setUserModifiedKeys] = useState<Set<string>>(new Set()); // Track which keys user changed
  
  // Loading/Error
  const [loading, setLoading] = useState(false);
  const [pipelinesLoading, setPipelinesLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedFileCount, setUploadedFileCount] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [fileInputKey, setFileInputKey] = useState(Date.now()); // Key to reset file inputs

  useEffect(() => {
    if (isAuthenticated) {
      fetchPipelines();
    }
  }, [isAuthenticated]);

  const fetchPipelines = async () => {
    try {
      const data = await api.pipelines.list();
      setPipelines(data);
      
      // If pipeline is preselected via URL, auto-select it
      if (preselectedPipelineId) {
        const preselected = data.find((p: Pipeline) => p.id === preselectedPipelineId);
        if (preselected) {
          handlePipelineSelect(preselected);
          setStep(2); // Skip to data step
        }
      }
    } catch (err) {
      console.error(err);
      setError('Failed to load pipelines');
    } finally {
      setPipelinesLoading(false);
    }
  };

  const handlePipelineSelect = (pipeline: Pipeline) => {
    setSelectedPipeline(pipeline);
    // Load default config from backend
    const defaults = pipeline.conf_defaults || {};
    setConfig(defaults);
    setDefaultConfig(defaults); // Store defaults to compare later
    setUserModifiedKeys(new Set()); // Reset user modifications
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

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const payload = {
        pipeline_id: selectedPipeline?.id,
        input_uri: inputUri,
        overrides: config
      };
      
      await api.jobs.create(payload);
      router.push('/jobs');
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  const canProceed = () => {
    switch (step) {
      case 1: return !!selectedPipeline;
      case 2: return !!inputUri && inputUri.startsWith('gs://');
      case 3: return true;
      case 4: return true;
      default: return false;
    }
  };

  return (
    <AppLayout title="New Annotation Job" description="Create a new annotation job">
      <div className="max-w-4xl mx-auto">
        {/* Step Indicator */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            {steps.map((s, index) => (
              <div key={s.id} className="flex items-center">
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      "flex h-10 w-10 items-center justify-center rounded-full border-2 transition-all duration-200",
                      step > s.id
                        ? "border-emerald-500 bg-emerald-500 text-white"
                        : step === s.id
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-card text-muted-foreground"
                    )}
                  >
                    {step > s.id ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <span className="text-sm font-semibold">{s.id}</span>
                    )}
                  </div>
                  <div className="mt-2 text-center">
                    <p className={cn(
                      "text-sm font-medium",
                      step >= s.id ? "text-foreground" : "text-muted-foreground"
                    )}>
                      {s.name}
                    </p>
                    <p className="text-xs text-muted-foreground hidden sm:block">
                      {s.description}
                    </p>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      "hidden sm:block w-24 h-0.5 mx-4 mt-[-24px]",
                      step > s.id ? "bg-emerald-500" : "bg-border"
                    )}
                  />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 rounded-lg bg-destructive/10 border border-destructive/20 flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-destructive">Error</p>
              <p className="text-sm text-destructive/80">{error}</p>
            </div>
          </div>
        )}

        {/* Step Content */}
        <Card className="overflow-hidden">
          <CardContent className="p-0">
            {/* STEP 1: PIPELINE SELECTION */}
            {step === 1 && (
              <div className="p-6">
                <div className="mb-6">
                  <h2 className="text-xl font-semibold text-foreground">Select Annotation Model</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Choose the AI model that best fits your annotation needs
                  </p>
                </div>

                {pipelinesLoading ? (
                  <div className="flex items-center justify-center py-16">
                    <div className="flex flex-col items-center gap-4">
                      <Loader2 className="h-8 w-8 animate-spin text-primary" />
                      <p className="text-sm text-muted-foreground">Loading available models...</p>
                    </div>
                  </div>
                ) : pipelines.length === 0 ? (
                  <div className="text-center py-16">
                    <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
                      <AlertCircle className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <p className="text-lg font-medium text-foreground">No models available</p>
                    <p className="text-sm text-muted-foreground mt-1">Please contact support</p>
                  </div>
                ) : (
                  <div className="space-y-6">
                    {/* 3D Pipelines */}
                    {pipelines3D.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-3">
                          <Box className="h-5 w-5 text-primary" />
                          <h3 className="font-medium text-foreground">3D Pipelines</h3>
                          <Badge variant="secondary" className="text-xs">{pipelines3D.length}</Badge>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {pipelines3D.map((p) => {
                            const Icon = getPipelineIcon(p);
                            const isSelected = selectedPipeline?.id === p.id;
                            const info = getPipelineDisplayInfo(p);
                            
                            return (
                              <button
                                key={p.id}
                                onClick={() => handlePipelineSelect(p)}
                                className={cn(
                                  "relative p-5 rounded-xl border-2 text-left transition-all duration-200",
                                  "hover:border-primary/50 hover:bg-secondary/30",
                                  isSelected 
                                    ? "border-primary bg-primary/5 ring-2 ring-primary/20" 
                                    : "border-border bg-card"
                                )}
                              >
                                {isSelected && (
                                  <div className="absolute top-3 right-3">
                                    <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                                      <Check className="h-4 w-4 text-white" />
                                    </div>
                                  </div>
                                )}
                                
                                <div className={cn(
                                  "w-12 h-12 rounded-xl flex items-center justify-center mb-4",
                                  isSelected ? "bg-primary/10" : "bg-secondary"
                                )}>
                                  <Icon className={cn(
                                    "h-6 w-6",
                                    isSelected ? "text-primary" : "text-muted-foreground"
                                  )} />
                                </div>
                                
                                <h3 className="font-semibold text-foreground mb-1">
                                  {info.displayName}
                                </h3>
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                  {info.description}
                                </p>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* 2D Pipelines */}
                    {pipelines2D.length > 0 && (
                      <div>
                        <div className="flex items-center gap-2 mb-3">
                          <Image className="h-5 w-5 text-primary" />
                          <h3 className="font-medium text-foreground">2D Pipelines</h3>
                          <Badge variant="secondary" className="text-xs">{pipelines2D.length}</Badge>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          {pipelines2D.map((p) => {
                            const Icon = getPipelineIcon(p);
                            const isSelected = selectedPipeline?.id === p.id;
                            const info = getPipelineDisplayInfo(p);
                            
                            return (
                              <button
                                key={p.id}
                                onClick={() => handlePipelineSelect(p)}
                                className={cn(
                                  "relative p-5 rounded-xl border-2 text-left transition-all duration-200",
                                  "hover:border-primary/50 hover:bg-secondary/30",
                                  isSelected 
                                    ? "border-primary bg-primary/5 ring-2 ring-primary/20" 
                                    : "border-border bg-card"
                                )}
                              >
                                {isSelected && (
                                  <div className="absolute top-3 right-3">
                                    <div className="w-6 h-6 rounded-full bg-primary flex items-center justify-center">
                                      <Check className="h-4 w-4 text-white" />
                                    </div>
                                  </div>
                                )}
                                
                                <div className={cn(
                                  "w-12 h-12 rounded-xl flex items-center justify-center mb-4",
                                  isSelected ? "bg-primary/10" : "bg-secondary"
                                )}>
                                  <Icon className={cn(
                                    "h-6 w-6",
                                    isSelected ? "text-primary" : "text-muted-foreground"
                                  )} />
                                </div>
                                
                                <h3 className="font-semibold text-foreground mb-1">
                                  {info.displayName}
                                </h3>
                                <p className="text-sm text-muted-foreground line-clamp-2">
                                  {info.description}
                                </p>
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* STEP 2: DATA SOURCE */}
            {step === 2 && (
              <div className="p-6">
                <div className="mb-6">
                  <h2 className="text-xl font-semibold text-foreground">Input Data Source</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Upload data from local computer or provide GCS path
                  </p>
                </div>

                <div className="space-y-6">
                  {/* Selected Model Display */}
                  <div className="p-4 rounded-lg bg-secondary/30 border border-border flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                      <CheckCircle2 className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground uppercase tracking-wider">Selected Model</p>
                      <p className="font-medium text-foreground">{selectedPipeline?.display_name}</p>
                    </div>
                  </div>

                  {/* File Upload / GCS Path Toggle */}
                   <div className="space-y-4">
                    {/* Upload Options - Two columns */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Single/Multiple Files Upload */}
                      <div className={`border border-dashed border-border rounded-xl p-6 text-center transition-colors ${isUploading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-secondary/20 cursor-pointer'}`}>
                        <label className={`block ${isUploading ? 'pointer-events-none' : 'cursor-pointer'}`}>
                          <input
                            key={`files-${fileInputKey}`}
                            type="file"
                            multiple
                            accept="image/*,.zip"
                            className="hidden"
                            disabled={isUploading}
                            onChange={async (e) => {
                               if (e.target.files && e.target.files.length > 0 && !isUploading) {
                                 const filesToUpload = e.target.files;
                                 try {
                                   setIsUploading(true);
                                   setUploadProgress(0);
                                   setError('');
                                   setUploadedFileCount(0);
                                   
                                   if (filesToUpload.length === 1) {
                                     // Single file - use original endpoint
                                     const file = filesToUpload[0];
                                     const res = await api.utils.upload(file, (progress) => {
                                        setUploadProgress(progress);
                                     });
                                     setInputUri(res.gcs_path);
                                     setUploadedFileCount(1);
                                   } else {
                                     // Multiple files
                                     const res = await api.utils.uploadMultiple(filesToUpload, (progress) => {
                                        setUploadProgress(progress);
                                     });
                                     setInputUri(res.gcs_path);
                                     setUploadedFileCount(res.file_count);
                                   }
                                 } catch (err: any) {
                                   console.error(err);
                                   setError(err.response?.data?.detail || "Failed to upload files");
                                   setUploadedFileCount(0);
                                 } finally {
                                   setIsUploading(false);
                                   setFileInputKey(Date.now()); // Reset file input
                                 }
                               }
                            }}
                          />
                          <div className="flex flex-col items-center gap-2">
                            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                              <Image className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                              <p className="text-sm font-medium text-foreground">
                                {isUploading ? (
                                  <span className="flex items-center gap-2">
                                      {uploadProgress >= 95 ? "Processing..." : `Uploading... ${uploadProgress}%`}
                                  </span>
                                ) : "Upload Files"}
                              </p>
                              <p className="text-xs text-muted-foreground mt-1">
                                Select images or a zip file
                              </p>
                            </div>
                          </div>
                        </label>
                      </div>

                      {/* Folder Upload */}
                      <div className={`border border-dashed border-border rounded-xl p-6 text-center transition-colors ${isUploading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-secondary/20 cursor-pointer'}`}>
                        <label className={`block ${isUploading ? 'pointer-events-none' : 'cursor-pointer'}`}>
                          <input
                            key={`folder-${fileInputKey}`}
                            type="file"
                            className="hidden"
                            disabled={isUploading}
                            {...{ webkitdirectory: "", directory: "" } as any}
                            onChange={async (e) => {
                               if (e.target.files && e.target.files.length > 0 && !isUploading) {
                                 const filesToUpload = e.target.files;
                                 try {
                                   setIsUploading(true);
                                   setUploadProgress(0);
                                   setError('');
                                   setUploadedFileCount(0);
                                   
                                   const res = await api.utils.uploadMultiple(filesToUpload, (progress) => {
                                      setUploadProgress(progress);
                                   });
                                   setInputUri(res.gcs_path);
                                   setUploadedFileCount(res.file_count);
                                 } catch (err: any) {
                                   console.error(err);
                                   setError(err.response?.data?.detail || "Failed to upload folder");
                                   setUploadedFileCount(0);
                                 } finally {
                                   setIsUploading(false);
                                   setFileInputKey(Date.now()); // Reset file input
                                 }
                               }
                            }}
                          />
                          <div className="flex flex-col items-center gap-2">
                            <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
                              <FolderInput className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                              <p className="text-sm font-medium text-foreground">
                                {isUploading ? (
                                  <span className="flex items-center gap-2">
                                      {uploadProgress >= 95 ? "Processing..." : `Uploading... ${uploadProgress}%`}
                                  </span>
                                ) : "Upload Folder"}
                              </p>
                              <p className="text-xs text-muted-foreground mt-1">
                                Select an entire folder
                              </p>
                            </div>
                          </div>
                        </label>
                      </div>
                    </div>

                    {/* Upload Progress */}
                    {isUploading && (
                      <div className="p-4 rounded-lg bg-secondary/30 border border-border">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-foreground">
                            {uploadProgress >= 95 ? "Processing on server..." : "Uploading..."}
                          </span>
                          <span className="text-sm text-muted-foreground">{uploadProgress}%</span>
                        </div>
                        <Progress value={uploadProgress} className="h-2" />
                        {uploadProgress >= 95 && (
                          <p className="text-xs text-muted-foreground mt-2">
                            Files are being uploaded to cloud storage. This may take a moment...
                          </p>
                        )}
                      </div>
                    )}

                    {/* Upload Success */}
                    {!isUploading && uploadedFileCount > 0 && inputUri && (
                      <div className="p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                        <div className="flex items-center gap-2">
                          <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                          <span className="text-sm text-foreground">
                            Uploaded {uploadedFileCount} file{uploadedFileCount > 1 ? 's' : ''} successfully
                          </span>
                        </div>
                      </div>
                    )}

                    <div className="relative flex items-center py-2">
                      <div className="flex-grow border-t border-border"></div>
                      <span className="flex-shrink-0 mx-4 text-xs text-muted-foreground uppercase">OR</span>
                      <div className="flex-grow border-t border-border"></div>
                    </div>


                    {/* GCS Path Input */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-foreground">
                        GCS Input Path
                        </label>
                        <div className="relative">
                        <FolderInput className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                        <Input
                            placeholder="gs://your-bucket/path/to/data/"
                            value={inputUri}
                            onChange={(e) => setInputUri(e.target.value)}
                            className="pl-12 h-12 text-base font-mono"
                        />
                        </div>
                        <p className="text-xs text-muted-foreground">
                        Enter the full path to your images, videos, or point cloud data
                        </p>
                    </div>
                  </div>


                  {/* Quick Examples */}
                  <div className="pt-4 border-t border-border">
                    <p className="text-xs text-muted-foreground mb-2">Examples:</p>
                    <div className="flex flex-wrap gap-2">
                      {[
                        'gs://data-sets-caliperai/images/',
                        'gs://data-sets-caliperai/lidar/',
                      ].map((example) => (
                        <button
                          key={example}
                          onClick={() => setInputUri(example)}
                          className="px-3 py-1.5 rounded-lg bg-secondary text-xs font-mono text-muted-foreground hover:text-foreground transition-colors"
                        >
                          {example}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* STEP 3: CONFIGURATION */}
            {step === 3 && (
              <div className="p-6">
                <div className="mb-6">
                  <h2 className="text-xl font-semibold text-foreground">Configuration</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Adjust parameters for the annotation model (defaults are pre-filled)
                  </p>
                </div>

                <div className="space-y-6">
                  {/* Configurable Fields - Easy Edit */}
                  {selectedPipeline?.conf_schema?.threshold_fields && 
                   Object.keys(selectedPipeline.conf_schema.threshold_fields).length > 0 ? (
                    <div className="space-y-4">
                      <h3 className="text-sm font-medium text-foreground flex items-center gap-2">
                        <Settings className="h-4 w-4" />
                        Model Parameters
                      </h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {Object.entries(selectedPipeline.conf_schema.threshold_fields).map(([key, defaultValue]) => {
                          // Parse nested key path
                          const keyParts = key.split('.');
                          const fieldName = keyParts[keyParts.length - 1];
                          const displayName = fieldName
                            .replace(/_/g, ' ')
                            .replace(/\b\w/g, l => l.toUpperCase());
                          
                          // Determine field type and constraints
                          const isBatchSize = fieldName.toLowerCase() === 'batch_size';
                          const isThreshold = fieldName.toLowerCase().includes('threshold') || 
                                              fieldName.toLowerCase().includes('confidence');
                          
                          // Get current value from config
                          const getCurrentValue = (): number => {
                            let current: any = config;
                            for (const part of keyParts) {
                              if (current && typeof current === 'object') {
                                current = current[part];
                              } else {
                                return defaultValue as number;
                              }
                            }
                            return current ?? defaultValue;
                          };
                          
                          // Set value in nested config and track modification
                          const setNestedValue = (newValue: number) => {
                            const newConfig = JSON.parse(JSON.stringify(config));
                            let current = newConfig;
                            for (let i = 0; i < keyParts.length - 1; i++) {
                              if (!current[keyParts[i]]) {
                                current[keyParts[i]] = {};
                              }
                              current = current[keyParts[i]];
                            }
                            current[keyParts[keyParts.length - 1]] = newValue;
                            setConfig(newConfig);
                            
                            // Track this key as user-modified
                            setUserModifiedKeys(prev => new Set(prev).add(key));
                          };
                          
                          return (
                            <ConfigNumberInput
                              key={key}
                              label={displayName}
                              value={getCurrentValue()}
                              onChange={setNestedValue}
                              isBatchSize={isBatchSize}
                              isThreshold={isThreshold}
                            />
                          );
                        })}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <Settings className="h-8 w-8 mx-auto mb-3 opacity-50" />
                      <p>Using default configuration for this pipeline</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* STEP 4: REVIEW */}
            {step === 4 && (
              <div className="p-6">
                <div className="mb-6">
                  <h2 className="text-xl font-semibold text-foreground">Review & Launch</h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    Verify your job configuration before starting
                  </p>
                </div>

                <div className="space-y-4">
                  {/* Summary Cards */}
                  <div className="rounded-xl border border-border overflow-hidden divide-y divide-border">
                    {/* Model */}
                    <div className="p-4 flex items-center justify-between bg-card">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
                          <Sparkles className="h-5 w-5 text-violet-400" />
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground uppercase tracking-wider">Model</p>
                          <p className="font-medium text-foreground">
                            {selectedPipeline ? getPipelineDisplayInfo(selectedPipeline).displayName : ''}
                          </p>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => setStep(1)}>
                        Edit
                      </Button>
                    </div>
                    
                    {/* Input Path */}
                    <div className="p-4 flex items-center justify-between bg-card">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                          <FolderInput className="h-5 w-5 text-blue-400" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs text-muted-foreground uppercase tracking-wider">Input Path</p>
                          <p className="font-mono text-sm text-foreground truncate max-w-md">{inputUri}</p>
                        </div>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => setStep(2)}>
                        Edit
                      </Button>
                    </div>
                    
                    {/* Config */}
                    <div className="p-4 bg-card">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                            <Settings className="h-5 w-5 text-amber-400" />
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground uppercase tracking-wider">Configuration</p>
                            <p className="text-sm text-muted-foreground">
                              {userModifiedKeys.size > 0 ? `${userModifiedKeys.size} parameter(s) customized` : 'Using defaults'}
                            </p>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => setStep(3)}>
                          Edit
                        </Button>
                      </div>
                      {userModifiedKeys.size > 0 && selectedPipeline?.conf_schema?.threshold_fields && (
                        <div className="grid grid-cols-2 gap-3 bg-secondary/30 rounded-lg p-4">
                          {Array.from(userModifiedKeys).map((key) => {
                            const keyParts = key.split('.');
                            const fieldName = keyParts[keyParts.length - 1];
                            const displayName = fieldName
                              .replace(/_/g, ' ')
                              .replace(/\b\w/g, l => l.toUpperCase());
                            
                            // Get current value from config
                            let currentValue: any = config;
                            for (const part of keyParts) {
                              if (currentValue && typeof currentValue === 'object') {
                                currentValue = currentValue[part];
                              }
                            }
                            
                            return (
                              <div key={key} className="flex justify-between items-center text-sm">
                                <span className="text-muted-foreground">{displayName}</span>
                                <span className="font-mono text-foreground">{String(currentValue)}</span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Navigation Footer */}
            <div className="px-6 py-4 bg-secondary/30 border-t border-border flex items-center justify-between">
              <Button 
                variant="ghost" 
                onClick={() => step === 1 ? router.push('/jobs') : setStep(step - 1)}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                {step === 1 ? 'Cancel' : 'Back'}
              </Button>
              
              {step < 4 ? (
                <Button 
                  onClick={() => setStep(step + 1)} 
                  disabled={!canProceed()}
                >
                  Continue
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              ) : (
                <Button 
                  onClick={handleSubmit} 
                  disabled={loading}
                  className="min-w-[140px]"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Starting...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Launch Job
                    </>
                  )}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </AppLayout>
  );
}

function LoadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <Loader2 className="w-8 h-8 animate-spin text-primary" />
    </div>
  );
}

export default function NewJobPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <NewJobContent />
    </Suspense>
  );
}
