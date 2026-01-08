import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Auto-Annotation Orchestrator',
  description: 'Manage specific auto-annotation pipelines',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
