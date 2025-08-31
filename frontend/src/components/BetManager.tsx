'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

export interface PlacedBet {
  id: string
  fighter: string
  opponent: string
  book: string
  odds: number
  bet_amount: number
  unit_size: number
  ev_percentage: number
  confidence_score: number
  kelly_recommended: number
  placed_date: string
  fight_date: string
  status: 'pending' | 'won' | 'lost'
  result_amount?: number
  settled_date?: string
  notes?: string
}

interface BetManagerContextType {
  bets: PlacedBet[]
  addBet: (bet: Omit<PlacedBet, 'id' | 'placed_date' | 'status'>) => void
  updateBet: (id: string, updates: Partial<PlacedBet>) => void
  deleteBet: (id: string) => void
  settleBet: (id: string, won: boolean, resultAmount?: number) => void
}

const BetManagerContext = createContext<BetManagerContextType | null>(null)

export function BetManagerProvider({ children }: { children: ReactNode }) {
  const [bets, setBets] = useState<PlacedBet[]>(() => {
    // Try to load from localStorage on initialization
    if (typeof window !== 'undefined') {
      try {
        const savedBets = localStorage.getItem('mma-bets')
        if (savedBets) {
          const parsedBets = JSON.parse(savedBets)
          console.log('Loaded bets from localStorage:', parsedBets.length)
          return parsedBets
        }
      } catch (error) {
        console.error('Error loading bets from localStorage:', error)
      }
    }
    
    // Fallback to sample data if no saved bets
    console.log('No saved bets found, using sample data')
    return [
      {
        id: '1',
        fighter: 'Jon Jones',
        opponent: 'Tom Aspinall',
        book: 'DraftKings',
        odds: -135,
        bet_amount: 22.0,
        unit_size: 2.2,
        ev_percentage: 2.2,
        confidence_score: 68.1,
        kelly_recommended: 2.2,
        placed_date: new Date().toISOString(),
        fight_date: '2024-11-16',
        status: 'pending',
        notes: 'Original sample bet'
      }
    ]
  })

  // Save to localStorage whenever bets change
  useEffect(() => {
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem('mma-bets', JSON.stringify(bets))
        console.log('Saved bets to localStorage:', bets.length)
      } catch (error) {
        console.error('Error saving bets to localStorage:', error)
      }
    }
  }, [bets])

  const addBet = (newBet: Omit<PlacedBet, 'id' | 'placed_date' | 'status'>) => {
    const bet: PlacedBet = {
      ...newBet,
      id: Date.now().toString(),
      placed_date: new Date().toISOString(),
      status: 'pending'
    }
    
    setBets(prev => {
      const updated = [...prev, bet]
      console.log('Added bet:', bet.fighter, 'Total bets now:', updated.length)
      return updated
    })
  }

  const updateBet = (id: string, updates: Partial<PlacedBet>) => {
    setBets(prev => prev.map(bet => 
      bet.id === id ? { ...bet, ...updates } : bet
    ))
    console.log('Updated bet:', id, updates)
  }

  const deleteBet = (id: string) => {
    setBets(prev => prev.filter(bet => bet.id !== id))
    console.log('Deleted bet:', id)
  }

  const settleBet = (id: string, won: boolean, resultAmount?: number) => {
    const bet = bets.find(b => b.id === id)
    if (!bet) return

    let calculatedResult = resultAmount
    if (!calculatedResult) {
      // Calculate payout based on odds
      if (won) {
        if (bet.odds > 0) {
          calculatedResult = bet.bet_amount + (bet.bet_amount * (bet.odds / 100))
        } else {
          calculatedResult = bet.bet_amount + (bet.bet_amount * (100 / Math.abs(bet.odds)))
        }
      } else {
        calculatedResult = 0 // Lost the stake
      }
    }

    updateBet(id, {
      status: won ? 'won' : 'lost',
      result_amount: calculatedResult,
      settled_date: new Date().toISOString()
    })
  }

  return (
    <BetManagerContext.Provider value={{
      bets,
      addBet,
      updateBet,
      deleteBet,
      settleBet
    }}>
      {children}
    </BetManagerContext.Provider>
  )
}

export function useBetManager() {
  const context = useContext(BetManagerContext)
  if (!context) {
    throw new Error('useBetManager must be used within BetManagerProvider')
  }
  return context
}