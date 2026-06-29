import type { Metadata } from 'next';
import { Outfit } from 'next/font/google';
import './globals.css';
import { Toaster } from 'react-hot-toast';

const outfit = Outfit({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'PriceIQ — AI Pricing Intelligence Dashboard',
  description: 'AI-powered dynamic pricing with multi-agent recommendations and human-in-the-loop approval workflow.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${outfit.className} bg-[#050505] text-[#FAFAFA] antialiased`}>
        {children}
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#111111',
              color: '#FAFAFA',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
            },
          }}
        />
      </body>
    </html>
  );
}
