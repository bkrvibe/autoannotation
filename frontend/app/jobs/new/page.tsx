'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { AppLayout } from '@/components/layout';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
  AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Pipeline {
  id: string;
  display_name: string;
  description: string;
  tags: string[];
  conf_schema: any;
  conf_defaults: any;
}

const steps = [
  { id: 1, name: 'Model', description: 'Choose annotation model' },
  { id: 2, name: 'Data', description: 'Input source' },
  { id: 3, name: 'Config', description: 'Parameters' },
  { id: 4, name: 'Launch', description: 'Review & run' },
];

function getPipelineIcon(pipeline: Pipeline) {
  const id = pipeline.id.toLowerCase();
  if (id.includes('3d') || id.includes('point_cloud')) return Box;
  if (id.includes('segmentation')) return Layers;
  if (id.includes('2d') || id.includes('image')) return Image;
  return Sparkles;
}

export default function NewJobPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  
  // Form State
  const [inputUri, setInputUri] = useState('');
  const [config, setConfig] = useState<any>({});
  
  // Loading/Error
  const [loading, setLoading] = useState(false);
  const [pipelinesLoading, setPipelinesLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
    } else {
      fetchPipelines();
    }
  }, [router]);

  const fetchPipelines = async () => {
    try {
      const data = await api.pipelines.list();
      setPipelines(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load pipelines');
    } finally {
      setPipelinesLoading(false);
    }
  };

  const handlePipelineSelect = (pipeline: Pipeline) => {
    setSelectedPipeline(pipeline);
    setConfig(pipeline.conf_defaults || {});
  };

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
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {pipelines.map((p) => {
                      const Icon = getPipelineIcon(p);
                      const isSelected = selectedPipeline?.id === p.id;
                      
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
                            {p.display_name}
                          </h3>
                          <p className="text-sm text-muted-foreground line-clamp-2">
                            {p.description}
                          </p>
                          
                          {p.tags && p.tags.length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-3">
                              {p.tags.slice(0, 3).map((tag) => (
                                <span 
                                  key={tag} 
                                  className="px-2 py-0.5 rounded-full bg-secondary text-xs text-muted-foreground"
                                >
                                  {tag}
                                </span>
                              ))}
                            </div>
                          )}
                        </button>
                      );
                    })}
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
                    Specify the location of your data in Google Cloud Storage
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
                    Customize pipeline parameters (optional - defaults are pre-filled)
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-foreground flex items-center gap-2">
                      <Settings className="h-4 w-4" />
                      Configuration Overrides
                    </label>
                    <textarea
                      rows={14}
                      className={cn(
                        "w-full rounded-lg border border-border bg-[#0c0e14] px-4 py-3",
                        "text-sm font-mono text-foreground",
                        "focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary",
                        "placeholder:text-muted-foreground resize-none"
                      )}
                      value={JSON.stringify(config, null, 2)}
                      onChange={(e) => {
                        try {
                          setConfig(JSON.parse(e.target.value));
                        } catch {
                          // Allow typing invalid JSON
                        }
                      }}
                    />
                    <p className="text-xs text-muted-foreground">
                      Modify the JSON configuration to override default pipeline settings
                    </p>
                  </div>
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
                          <p className="font-medium text-foreground">{selectedPipeline?.display_name}</p>
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
                            <p className="text-sm text-muted-foreground">{Object.keys(config).length} parameters</p>
                          </div>
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => setStep(3)}>
                          Edit
                        </Button>
                      </div>
                      <pre className="text-xs bg-[#0c0e14] rounded-lg p-4 overflow-x-auto text-muted-foreground">
                        {JSON.stringify(config, null, 2)}
                      </pre>
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
