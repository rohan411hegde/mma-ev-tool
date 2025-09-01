'use client'

import { useState, useEffect } from 'react'
import EventCard from '@/components/EventCard'
import EVOpportunities from '@/components/EVOpportunities'
import { TrendingUp, Target, Calendar, BarChart3 } from 'lucide-react'
import Link from 'next/link'


interface FighterOdds {
  book: string
  fighter1_odds: number
  fighter2_odds: number
}

interface Fight {
  fighter1: string
  fighter2: string
  event_name: string
  event_date: string
  weight_class: string
  odds: FighterOdds[]
  scraped_at: string
}

interface EVOpportunity {
  fighter: string
  book: string
  ev_percentage: number
  confidence_score: number
  sharp_consensus_prob: number
  square_prob: number
  recommendation: string
  fight_info: string
  kelly_size?: number
  kelly_dollars?: number
  kelly_units?: number
  kelly_category?: string
}

export default function Home() {
  const [fights, setFights] = useState<Fight[]>([])
  const [evOpportunities, setEVOpportunities] = useState<EVOpportunity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      
      // Load fights from API
      const fightsResponse = await fetch('https://mma-ev-tool.onrender.com/api/fights')
      const fightsData = await fightsResponse.json()
      
      // Load EV opportunities from API  
      const evResponse = await fetch('https://mma-ev-tool.onrender.com/api/ev-opportunities')
      const evData = await evResponse.json()
      
      if (fightsData.success) {
        setFights(fightsData.fights)
      }
      
      if (evData.success) {
        setEVOpportunities(evData.opportunities)
      }
      
      setLoading(false)
      
    } catch (error) {
      console.error('Error loading data:', error)
      
      // Fallback to sample data if API fails
      const sampleFights: Fight[] = [
        {
          fighter1: "Jon Jones",
          fighter2: "Tom Aspinall", 
          event_name: "UFC 309",
          event_date: "2024-11-16",
          weight_class: "Heavyweight",
          odds: [
            { book: "Pinnacle", fighter1_odds: -150, fighter2_odds: 130 },
            { book: "DraftKings", fighter1_odds: -135, fighter2_odds: 115 }
          ],
          scraped_at: new Date().toISOString()
        }
      ]

      const sampleEVs: EVOpportunity[] = [
        {
          fighter: "Jon Jones",
          book: "DraftKings", 
          ev_percentage: 2.2,
          confidence_score: 68.1,
          sharp_consensus_prob: 57.5,
          square_prob: 55.3,
          recommendation: "✅ GOOD BET",
          fight_info: "Jon Jones vs Tom Aspinall",
          kelly_size: 2.2,
          kelly_dollars: 22.0,
          kelly_units: 2.2,
          kelly_category: "💪 MEDIUM"
        }
      ]

      setFights(sampleFights)
      setEVOpportunities(sampleEVs)
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto"></div>
          <p className="text-gray-300 mt-4">Loading fight data...</p>
        </div>
      </div>
    )
  }

  const totalEVOps = evOpportunities.length
  const strongBets = evOpportunities.filter(ev => ev.ev_percentage >= 2.5).length
  const avgEV = evOpportunities.length > 0 
    ? evOpportunities.reduce((sum, ev) => sum + ev.ev_percentage, 0) / evOpportunities.length 
    : 0

  // Group fights by event
  const groupedFights = fights.reduce((acc, fight) => {
    const eventName = fight.event_name
    if (!acc[eventName]) {
      acc[eventName] = {
        eventName: eventName,
        eventDate: fight.event_date,
        fights: []
      }
    }
    acc[eventName].fights.push(fight)
    return acc
  }, {} as Record<string, { eventName: string; eventDate: string; fights: Fight[] }>)

  const events = Object.values(groupedFights)

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      {/* Header */}
      <header className="bg-black/20 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                🥊 <span>MMA EV Tool</span>
              </h1>
              <p className="text-gray-300 mt-1">Sharp vs Square Betting Analysis</p>
            </div>
            <div className="flex items-center gap-6">
              <nav className="flex items-center gap-4">
               <Link href="/" className="text-white hover:text-orange-400 font-medium">Dashboard</Link>
                <a href="/tracking" className="text-gray-300 hover:text-orange-400 font-medium">Bet Tracking</a>
              </nav>
              <div className="text-right">
                <p className="text-gray-300 text-sm">Last Updated</p>
                <p className="text-white font-medium">
                  {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Stats Bar */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-black/30 backdrop-blur-sm rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-300 text-sm">Total Opportunities</p>
                <p className="text-2xl font-bold text-white">{totalEVOps}</p>
              </div>
              <Target className="h-8 w-8 text-orange-500" />
            </div>
          </div>

          <div className="bg-black/30 backdrop-blur-sm rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-300 text-sm">Strong Bets</p>
                <p className="text-2xl font-bold text-green-400">{strongBets}</p>
              </div>
              <TrendingUp className="h-8 w-8 text-green-400" />
            </div>
          </div>

          <div className="bg-black/30 backdrop-blur-sm rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-300 text-sm">Avg EV Edge</p>
                <p className="text-2xl font-bold text-blue-400">+{avgEV.toFixed(1)}%</p>
              </div>
              <BarChart3 className="h-8 w-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-black/30 backdrop-blur-sm rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-300 text-sm">Active Events</p>
                <p className="text-2xl font-bold text-white">{fights.length}</p>
              </div>
              <Calendar className="h-8 w-8 text-purple-400" />
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Fight Cards */}
          <div className="lg:col-span-2">
            <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Upcoming Events
            </h2>
            <div className="space-y-6">
              {events.map((event, index) => (
                <EventCard 
                  key={event.eventName}
                  eventName={event.eventName}
                  eventDate={event.eventDate}
                  fights={event.fights}
                  isDefaultOpen={index === 0} // Only first event open by default
                />
              ))}
            </div>
          </div>

          {/* EV Opportunities Sidebar */}
          <div>
            <EVOpportunities opportunities={evOpportunities} />
          </div>
        </div>
      </div>
    </div>
  )
}