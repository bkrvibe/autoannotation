"use client";

import { ReactNode } from "react";
import Link from "next/link";
import Image from "next/image";
import { Sidebar } from "./Sidebar";
import { Navbar } from "./Navbar";

interface AppLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
}

export function AppLayout({ children, title, description }: AppLayoutProps) {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background">
      {/* Unified Banner with Logo - Seamless */}
      <div className="bg-background z-50">
        <div className="flex items-center justify-between px-5 py-3">
          <Link href="/dashboard" className="flex items-center">
            <Image 
              src="/logo_light.png" 
              alt="CaliperAI Logo" 
              width={180} 
              height={40}
              className="h-9 w-auto drop-shadow-lg"
              priority
            />
          </Link>
          <p className="font-orbitron font-bold text-sm tracking-[0.25em] uppercase bg-gradient-to-r from-violet-400 via-purple-400 to-violet-400 bg-clip-text text-transparent drop-shadow-lg">
            The Annotation Dark Factory
          </p>
          <div className="w-[180px]"></div> {/* Spacer for centering */}
        </div>
      </div>
      
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <Navbar title={title} description={description} />
          <main className="flex-1 overflow-y-auto">
            <div className="container max-w-7xl mx-auto p-6">
              {children}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
