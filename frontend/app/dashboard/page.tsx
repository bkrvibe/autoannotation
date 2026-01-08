'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';

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
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<Job[]>([]);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
    } else {
      fetchJobs();
    }
  }, [router]);

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

  if (loading) {
    return <div className="p-8">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-zinc-900">
      <nav className="bg-white shadow dark:bg-zinc-800">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 justify-between">
            <div className="flex">
              <div className="flex flex-shrink-0 items-center">
                <span className="font-bold text-xl text-indigo-600">AutoAnn</span>
              </div>
              <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                <a href="#" className="border-indigo-500 text-gray-900 inline-flex items-center border-b-2 px-1 pt-1 text-sm font-medium dark:text-white">
                  Jobs
                </a>
                <a href="#" className="border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 inline-flex items-center border-b-2 px-1 pt-1 text-sm font-medium dark:text-gray-300">
                  Pipelines
                </a>
              </div>
            </div>
            <div className="flex items-center">
              <button
                onClick={() => {
                  localStorage.removeItem('token');
                  router.push('/login');
                }}
                className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <div className="py-10">
        <header>
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <h1 className="text-3xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white">
              Job History
            </h1>
          </div>
        </header>
        <main>
          <div className="mx-auto max-w-7xl sm:px-6 lg:px-8">
            <div className="px-4 py-8 sm:px-0">
              
              <div className="mb-4 flex justify-end">
                 <button
                    onClick={() => router.push('/dashboard/create-job')}
                    className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
                 >
                    Create New Job
                 </button>
              </div>

              {jobs.length === 0 ? (
                <div className="rounded-lg border-4 border-dashed border-gray-200 p-12 text-center h-96 dark:border-zinc-700 flex items-center justify-center">
                   <div>
                       <p className="text-gray-500 dark:text-gray-400">No jobs found.</p>
                       <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">Start a new run to see it here.</p>
                   </div>
                </div>
              ) : (
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 sm:rounded-lg">
                  <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-zinc-800">
                      <tr>
                        <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 dark:text-white sm:pl-6">ID</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Pipeline</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Status</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Input</th>
                        <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900 dark:text-white">Created At</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200 bg-white dark:bg-zinc-900 dark:divide-gray-700">
                      {jobs.map((job) => (
                        <tr key={job.id}>
                          <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 dark:text-white sm:pl-6">{job.id}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-300">{job.pipeline_id}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm">
                            <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
                              job.status === 'success' ? 'bg-green-50 text-green-700 ring-green-600/20' : 
                              job.status === 'failed' ? 'bg-red-50 text-red-700 ring-red-600/20' : 
                              'bg-yellow-50 text-yellow-800 ring-yellow-600/20'
                            }`}>
                              {job.status}
                            </span>
                          </td>
                           <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-300 max-w-xs truncate">{job.input_uri}</td>
                          <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500 dark:text-gray-300">
                            {new Date(job.created_at).toLocaleString()}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
