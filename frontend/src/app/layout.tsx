import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { BetManagerProvider } from '@/components/BetManager'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'MMA EV Tool',
  description: 'Sharp vs Square Betting Analysis',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <BetManagerProvider>
          {children}
        </BetManagerProvider>
      </body>
    </html>
  )
}