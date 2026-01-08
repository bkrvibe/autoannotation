'use client';
import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-50 dark:bg-zinc-900">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex flex-col gap-8">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
          Auto-Annotation Orchestrator
        </h1>
        <p className="text-xl text-gray-600 dark:text-gray-300 text-center max-w-2xl">
          Secure, multi-tenant orchestration for your 2D/3D auto-annotation pipelines.
        </p>
        
        <div className="flex gap-4">
          <Link href="/login" className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600">
            Get Started
          </Link>
        </div>
      </div>
    </main>
  );
}
