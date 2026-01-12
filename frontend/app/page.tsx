'use client';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Bot, Zap, Shield, BarChart3, ArrowRight, Sparkles, Box, Image, Play, CheckCircle2 } from 'lucide-react';

export default function Home() {
  const features = [
    {
      icon: Bot,
      title: 'AI-Powered Annotation',
      description: 'Leverage state-of-the-art models for automatic 2D and 3D annotation with high accuracy.',
    },
    {
      icon: Zap,
      title: 'High Performance',
      description: 'Process large datasets efficiently with Apache Airflow orchestration at scale.',
    },
    {
      icon: Shield,
      title: 'Enterprise Security',
      description: 'Secure, multi-tenant architecture with role-based access control and audit logs.',
    },
    {
      icon: BarChart3,
      title: 'Real-time Monitoring',
      description: 'Track job progress and view detailed analytics dashboards in real-time.',
    },
  ];

  const pipelines = [
    { icon: Image, name: '2D Auto Annotation', description: 'Object detection, segmentation, and labeling' },
    { icon: Box, name: '3D Point Cloud', description: 'LiDAR annotation and 3D bounding boxes' },
    { icon: Sparkles, name: 'SAM Segmentation', description: 'Segment Anything Model for precision' },
  ];

  const stats = [
    { value: '10M+', label: 'Annotations Processed' },
    { value: '99.9%', label: 'Uptime SLA' },
    { value: '50x', label: 'Faster Than Manual' },
    { value: '24/7', label: 'Support Available' },
  ];

  return (
    <main className="min-h-screen bg-[#0a0e1a]">
      {/* Gradient Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-600/20 rounded-full blur-3xl" />
        <div className="absolute top-1/3 right-1/4 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 left-1/3 w-72 h-72 bg-violet-500/10 rounded-full blur-3xl" />
      </div>

      {/* Header with Integrated Banner */}
      <header className="relative sticky top-0 z-50 bg-[#0a0e1a]/95 backdrop-blur-xl">
        {/* Unified Banner with Logo - Seamless */}
        <div className="">
          <div className="container mx-auto px-6 py-3 flex items-center justify-between">
            <Link href="/" className="flex items-center">
              <img 
                src="/logo_light.png" 
                alt="CaliperAI Logo" 
                className="h-9 w-auto drop-shadow-lg"
              />
            </Link>
            <p className="font-orbitron font-bold text-sm tracking-[0.25em] uppercase bg-gradient-to-r from-violet-400 via-purple-400 to-violet-400 bg-clip-text text-transparent drop-shadow-lg">
              The Annotation Dark Factory
            </p>
            <div className="w-[180px]"></div> {/* Spacer for centering */}
          </div>
        </div>
        {/* Nav Bar */}
        <div className="border-b border-white/5 bg-[#0a0e1a]/95 backdrop-blur-xl">
          <div className="container mx-auto px-6 py-4 flex items-center justify-end">
          <div className="flex items-center gap-4">
            <Link href="/login">
              <Button variant="ghost" className="text-slate-300 hover:text-white">
                Sign In
              </Button>
            </Link>
            <Link href="/login">
              <Button className="bg-violet-600 hover:bg-violet-500 text-white shadow-lg shadow-violet-500/25">
                Get Started
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative container mx-auto px-6 pt-24 pb-16 text-center">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-sm font-medium">
            <Sparkles className="w-4 h-4" />
            Enterprise-Ready Auto-Annotation Platform
          </div>
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight text-white">
            Automate Your
            <span className="block bg-gradient-to-r from-violet-400 via-violet-500 to-blue-400 bg-clip-text text-transparent">
              Annotation Workflows
            </span>
          </h1>
          <p className="text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Streamline your 2D/3D auto-annotation pipelines with enterprise-grade orchestration,
            powered by Apache Airflow and Google Cloud.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            <Link href="/login">
              <Button size="lg" className="bg-violet-600 hover:bg-violet-500 text-white text-base px-8 h-12 shadow-lg shadow-violet-500/25">
                Start Annotating
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline" className="text-base px-8 h-12 border-slate-700 text-slate-300 hover:bg-white/5 hover:text-white">
                <Play className="w-4 h-4 mr-2" />
                Watch Demo
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="relative mt-20 max-w-4xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 p-8 rounded-2xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/50 backdrop-blur-sm">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl md:text-4xl font-bold text-white">{stat.value}</div>
                <div className="text-sm text-slate-400 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pipelines Section */}
      <section className="relative container mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Available Pipelines
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Choose from our pre-configured annotation pipelines or create custom workflows.
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {pipelines.map((pipeline, index) => (
            <div
              key={index}
              className="group p-6 rounded-xl bg-gradient-to-br from-slate-800/50 to-slate-900/50 border border-slate-700/50 hover:border-violet-500/50 transition-all duration-300 cursor-pointer"
            >
              <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-violet-500/20 to-violet-600/20 flex items-center justify-center mb-4 group-hover:from-violet-500/30 group-hover:to-violet-600/30 transition-colors">
                <pipeline.icon className="w-7 h-7 text-violet-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{pipeline.name}</h3>
              <p className="text-sm text-slate-400">{pipeline.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features Section */}
      <section className="relative container mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Everything You Need
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            A complete solution for managing your auto-annotation pipelines at scale.
          </p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
          {features.map((feature, index) => (
            <div
              key={index}
              className="p-6 rounded-xl bg-gradient-to-br from-slate-800/30 to-slate-900/30 border border-slate-800 hover:border-slate-700 transition-colors"
            >
              <div className="w-12 h-12 rounded-lg bg-violet-500/10 flex items-center justify-center mb-4">
                <feature.icon className="w-6 h-6 text-violet-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{feature.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="relative container mx-auto px-6 py-16">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            How It Works
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto">
            Get started in minutes with our streamlined workflow.
          </p>
        </div>
        <div className="max-w-3xl mx-auto">
          <div className="space-y-6">
            {[
              { step: '01', title: 'Upload Your Data', description: 'Upload images or point clouds to Google Cloud Storage' },
              { step: '02', title: 'Select Pipeline', description: 'Choose from 2D, 3D, or custom annotation pipelines' },
              { step: '03', title: 'Configure & Launch', description: 'Customize parameters and start the annotation job' },
              { step: '04', title: 'Download Results', description: 'Get your annotated data in industry-standard formats' },
            ].map((item, index) => (
              <div key={index} className="flex items-start gap-6 p-6 rounded-xl bg-slate-800/30 border border-slate-800">
                <div className="flex-shrink-0 w-14 h-14 rounded-xl bg-violet-600/20 flex items-center justify-center">
                  <span className="text-lg font-bold text-violet-400">{item.step}</span>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white mb-1">{item.title}</h3>
                  <p className="text-slate-400">{item.description}</p>
                </div>
                {index < 3 && <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-1" />}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative container mx-auto px-6 py-16">
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-violet-600 to-violet-700 p-12 text-center">
          <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.05%22%3E%3Ccircle%20cx%3D%221%22%20cy%3D%221%22%20r%3D%221%22%2F%3E%3C%2Fg%3E%3C%2Fg%3E%3C%2Fsvg%3E')] opacity-100" />
          <div className="relative">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Ready to Get Started?</h2>
            <p className="text-lg text-violet-100 mb-8 max-w-xl mx-auto">
              Transform your annotation workflow with our enterprise-grade platform.
              Start your free trial today.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/login">
                <Button size="lg" className="bg-white hover:bg-slate-100 text-violet-600 font-semibold text-base px-8 h-12">
                  Launch Dashboard
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="border-white/30 text-white hover:bg-white/10 text-base px-8 h-12">
                  Contact Sales
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative border-t border-slate-800 mt-16">
        <div className="container mx-auto px-6 py-12">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-violet-600 rounded-xl flex items-center justify-center">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <div>
                  <span className="text-lg font-bold text-white">AutoAnn</span>
                  <span className="text-xs text-slate-500 block -mt-1">by Caliper AI</span>
                </div>
              </div>
              <p className="text-sm text-slate-400">
                Enterprise-grade auto-annotation platform for AI teams.
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#" className="hover:text-white transition-colors">Features</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API Reference</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#" className="hover:text-white transition-colors">About Us</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Careers</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#" className="hover:text-white transition-colors">Privacy Policy</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Terms of Service</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="pt-8 border-t border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-slate-500">
              © {new Date().getFullYear()} Caliper AI. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <a href="#" className="text-slate-400 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z"/></svg>
              </a>
              <a href="#" className="text-slate-400 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
              </a>
              <a href="#" className="text-slate-400 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </main>
  );
}
