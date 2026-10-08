import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { ClerkProvider } from '@clerk/nextjs';

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Dabu - AI Video Ad Creator",
  description: "Transform your scripts into perfectly synced TikTok ads in seconds. AI-powered video editing that matches your script to the perfect moments with frame-perfect timing.",
  keywords: ["TikTok ads", "video editing", "AI video", "script to video", "video automation", "Dabu", "content creation", "social media ads"],
  authors: [{ name: "Dabu" }],
  creator: "Dabu",
  publisher: "Dabu",
  applicationName: "Dabu",
  metadataBase: new URL('https://dabu.ai'),
  openGraph: {
    title: "Dabu - AI Video Ad Creator",
    description: "Create stunning TikTok ads with AI-powered script-to-video matching",
    url: 'https://dabu.ai',
    siteName: 'Dabu',
    type: 'website',
    locale: 'en_US',
    images: [
      {
        url: '/Vector.svg',
        width: 60,
        height: 66,
        alt: 'Dabu Logo',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Dabu - AI Video Ad Creator',
    description: 'Transform scripts into perfect TikTok ads with AI',
    creator: '@dabu',
    images: ['/Vector.svg'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  icons: {
    icon: "/Vector.svg",
    shortcut: "/Vector.svg",
    apple: "/Vector.svg",
  },
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      afterSignInUrl="/express-builder"
      afterSignUpUrl="/express-builder"
    >
      <html lang="en" className="dark">
        <body className={`${inter.className} bg-background text-foreground h-full`}>
          {children}
          <Toaster />
        </body>
      </html>
    </ClerkProvider>
  );
}
