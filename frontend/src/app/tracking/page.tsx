'use client'

import { ArrowLeft } from 'lucide-react'
import Link from 'next/link'
import EditableBetTable from '@/components/EditableBetTable'

export default function BetTrackingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      {/* Header */}
      <header className="bg-black/20 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link href="/" className="text-gray-300 hover:text-white">
                <ArrowLeft className="h-6 w-6" />
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                  📊 <span>Bet Tracking</span>
                </h1>
                <p className="text-gray-300 mt-1">Track your +EV plays and performance</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <nav className="flex items-center gap-4">
                <Link href="/" className="text-gray-300 hover:text-orange-400 font-medium">Dashboard</Link>
                <Link href="/tracking" className="text-white hover:text-orange-400 font-medium">Bet Tracking</Link>
              </nav>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto p-4">
        <EditableBetTable />
      </div>
    </div>
  )
}