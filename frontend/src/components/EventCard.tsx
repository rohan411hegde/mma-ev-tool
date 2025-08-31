'use client'

import { useState } from 'react'
import { ChevronDown, ChevronUp, Calendar, MapPin } from 'lucide-react'
import FightCard from './FightCard'

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

interface EventCardProps {
  eventName: string
  eventDate: string
  fights: Fight[]
  isDefaultOpen?: boolean
}

export default function EventCard({ eventName, eventDate, fights, isDefaultOpen = true }: EventCardProps) {
  const [isOpen, setIsOpen] = useState(isDefaultOpen)

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric', 
        month: 'long',
        day: 'numeric'
      })
    } catch {
      return dateString
    }
  }

  const getTotalBooks = () => {
    const allBooks = new Set<string>()
    fights.forEach(fight => {
      fight.odds.forEach(odd => allBooks.add(odd.book))
    })
    return allBooks.size
  }

  return (
    <div className="bg-black/40 backdrop-blur-sm rounded-lg border border-gray-700 mb-6">
      {/* Event Header - Clickable */}
      <div 
        className="p-6 cursor-pointer hover:bg-white/5 transition-colors border-b border-gray-700"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-orange-500/20 rounded-full w-12 h-12 flex items-center justify-center">
              <Calendar className="h-6 w-6 text-orange-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white mb-1">{eventName}</h2>
              <div className="flex items-center gap-4 text-gray-300 text-sm">
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {formatDate(eventDate)}
                </div>
                <div className="flex items-center gap-1">
                  <MapPin className="h-4 w-4" />
                  {fights.length} Fights
                </div>
                <div className="text-gray-400">
                  {getTotalBooks()} Sportsbooks
                </div>
              </div>
            </div>
          </div>

          {/* Stats Summary */}
          <div className="flex items-center gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-white">{fights.length}</div>
              <div className="text-xs text-gray-400">Fights</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-400">{getTotalBooks()}</div>
              <div className="text-xs text-gray-400">Books</div>
            </div>
            
            {/* Expand/Collapse Icon */}
            <div className="ml-4">
              {isOpen ? (
                <ChevronUp className="h-6 w-6 text-gray-400" />
              ) : (
                <ChevronDown className="h-6 w-6 text-gray-400" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Event Content - Collapsible */}
      {isOpen && (
        <div className="p-6">
          <div className="space-y-6">
            {fights.map((fight, index) => (
              <div key={index}>
                <FightCard fight={fight} />
              </div>
            ))}
          </div>

          {/* Event Footer */}
          <div className="mt-6 pt-4 border-t border-gray-700 flex justify-between items-center text-xs text-gray-400">
            <span>Last updated: {new Date(fights[0]?.scraped_at).toLocaleString()}</span>
            <span>{fights.length} fights • {getTotalBooks()} sportsbooks</span>
          </div>
        </div>
      )}
    </div>
  )
}