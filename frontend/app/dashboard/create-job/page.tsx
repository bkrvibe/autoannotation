'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

interface Pipeline {
  id: string;
  display_name: string;
  description: string;
  tags: string[];
  conf_schema: any;
  conf_defaults: any;
}

export default function CreateJobPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [pipelines, setPipelines] = useState<Pipeline[]>([]);
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null);
  
  // Form State
  const [inputUri, setInputUri] = useState('');
  const [config, setConfig] = useState<any>({});
  
  // Loading/Error
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchPipelines();
  }, []);

  const fetchPipelines = async () => {
    try {
      const data = await api.pipelines.list();
      setPipelines(data);
    } catch (err) {
      console.error(err);
      setError('Failed to load pipelines');
    }
  };

  const handlePipelineSelect = (pipeline: Pipeline) => {
    setSelectedPipeline(pipeline);
    setConfig(pipeline.conf_defaults); // Initialize with defaults
    setStep(2);
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
      router.push('/dashboard');
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-900 py-8">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <div className="md:flex md:items-center md:justify-between mb-8">
          <div className="min-w-0 flex-1">
            <h2 className="text-2xl font-bold leading-7 text-gray-900 dark:text-white sm:truncate sm:text-3xl sm:tracking-tight">
              Create New Annotation Job
            </h2>
          </div>
        </div>

        {/* Stepper */}
        <nav aria-label="Progress" className="mb-8">
          <ol role="list" className="space-y-4 md:flex md:space-x-8 md:space-y-0">
            {['Select Pipeline', 'Data Source', 'Configuration', 'Review'].map((label, index) => {
              const stepNum = index + 1;
              const isActive = step === stepNum;
              const isCompleted = step > stepNum;
              return (
                <li key={label} className="md:flex-1">
                  <div className={`group flex flex-col border-l-4 ${isActive ? 'border-indigo-600' : isCompleted ? 'border-green-600' : 'border-gray-200'} py-2 pl-4 md:border-l-0 md:border-t-4 md:pb-0 md:pl-0 md:pt-4`}>
                    <span className={`text-sm font-medium ${isActive ? 'text-indigo-600' : isCompleted ? 'text-green-600' : 'text-gray-500'}`}>
                      Step {stepNum}
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">{label}</span>
                  </div>
                </li>
              );
            })}
          </ol>
        </nav>

        <div className="bg-white shadow sm:rounded-lg dark:bg-zinc-800 p-6">
          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
               <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {/* STEP 1: PIPELINE SELECTION */}
          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">Available Pipelines</h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {pipelines.map((p) => (
                  <div
                    key={p.id}
                    onClick={() => handlePipelineSelect(p)}
                    className="relative flex items-center space-x-3 rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm focus-within:ring-2 focus-within:ring-indigo-500 focus-within:ring-offset-2 hover:border-gray-400 cursor-pointer dark:bg-zinc-700 dark:border-zinc-600"
                  >
                    <div className="min-w-0 flex-1">
                       <span className="absolute inset-0" aria-hidden="true" />
                       <p className="text-sm font-medium text-gray-900 dark:text-white">{p.display_name}</p>
                       <p className="truncate text-sm text-gray-500 dark:text-gray-300">{p.description}</p>
                       <div className="mt-2 flex gap-2">
                         {p.tags.map(tag => (
                           <span key={tag} className="inline-flex items-center rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-medium text-indigo-800">
                             {tag}
                           </span>
                         ))}
                       </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* STEP 2: DATA SOURCE */}
          {step === 2 && (
            <div className="space-y-6">
               <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">Data Source</h3>
               <div>
                 <label htmlFor="gcs_path" className="block text-sm font-medium leading-6 text-gray-900 dark:text-gray-200">
                   GCS Input Path (Direct)
                 </label>
                 <div className="mt-2">
                   <input
                     type="text"
                     name="gcs_path"
                     id="gcs_path"
                     className="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 dark:bg-zinc-900 dark:text-white dark:ring-zinc-700 pl-2"
                     placeholder="gs://my-bucket/my-images/"
                     value={inputUri}
                     onChange={(e) => setInputUri(e.target.value)}
                   />
                   <p className="mt-2 text-sm text-gray-500">
                     Enter the GCS path where your images or zip files are located. (Upload UI coming soon)
                   </p>
                 </div>
               </div>
               <div className="flex justify-end gap-3">
                  <button onClick={() => setStep(1)} className="text-sm font-semibold leading-6 text-gray-900 dark:text-gray-200">Back</button>
                  <button
                    onClick={() => setStep(3)}
                    disabled={!inputUri}
                    className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
                  >
                    Next
                  </button>
               </div>
            </div>
          )}

          {/* STEP 3: CONFIGURATION */}
          {step === 3 && (
            <div className="space-y-6">
               <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">Run Configuration</h3>
               <div className="space-y-4">
                 {/* Simple JSON Editor for MVP */}
                 <div>
                    <label className="block text-sm font-medium leading-6 text-gray-900 dark:text-gray-200">Overrides (JSON)</label>
                    <textarea
                      rows={10}
                      className="mt-2 block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 font-mono dark:bg-zinc-900 dark:text-white dark:ring-zinc-700 p-2"
                      value={JSON.stringify(config, null, 2)}
                      onChange={(e) => {
                         try {
                           setConfig(JSON.parse(e.target.value));
                         } catch (e) {
                           // Allow typing invalid json
                         }
                      }}
                    />
                 </div>
               </div>
               <div className="flex justify-end gap-3">
                  <button onClick={() => setStep(2)} className="text-sm font-semibold leading-6 text-gray-900 dark:text-gray-200">Back</button>
                  <button
                    onClick={() => setStep(4)}
                    className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
                  >
                    Next
                  </button>
               </div>
            </div>
          )}

          {/* STEP 4: REVIEW */}
          {step === 4 && (
            <div className="space-y-6">
              <h3 className="text-lg font-medium leading-6 text-gray-900 dark:text-white">Review & Submit</h3>
              
              <dl className="divide-y divide-gray-100 dark:divide-zinc-700">
                <div className="px-4 py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
                  <dt className="text-sm font-medium leading-6 text-gray-900 dark:text-gray-200">Pipeline</dt>
                  <dd className="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0 dark:text-gray-300">{selectedPipeline?.display_name}</dd>
                </div>
                <div className="px-4 py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
                  <dt className="text-sm font-medium leading-6 text-gray-900 dark:text-gray-200">Input Path</dt>
                  <dd className="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0 dark:text-gray-300">{inputUri}</dd>
                </div>
                <div className="px-4 py-3 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-0">
                  <dt className="text-sm font-medium leading-6 text-gray-900 dark:text-gray-200">Config</dt>
                  <dd className="mt-1 text-sm leading-6 text-gray-700 sm:col-span-2 sm:mt-0 dark:text-gray-300">
                    <pre className="whitespace-pre-wrap font-mono text-xs">{JSON.stringify(config, null, 2)}</pre>
                  </dd>
                </div>
              </dl>

              <div className="flex justify-end gap-3">
                  <button onClick={() => setStep(3)} className="text-sm font-semibold leading-6 text-gray-900 dark:text-gray-200">Back</button>
                  <button
                    onClick={handleSubmit}
                    disabled={loading}
                    className="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50"
                  >
                    {loading ? 'Starting...' : 'Start Job'}
                  </button>
               </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
