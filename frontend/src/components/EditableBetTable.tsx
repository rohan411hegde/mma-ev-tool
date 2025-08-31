'use client'

import { useState } from 'react'
import { CheckCircle, XCircle, Clock, Edit2, Save, X, Trash2 } from 'lucide-react'
import { useBetManager, PlacedBet } from './BetManager'

export default function EditableBetTable() {
  const { bets, updateBet, deleteBet, settleBet } = useBetManager()
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValues, setEditValues] = useState<Partial<PlacedBet>>({})

  const startEditing = (bet: PlacedBet) => {
    setEditingId(bet.id)
    setEditValues(bet)
  }

  const cancelEditing = () => {
    setEditingId(null)
    setEditValues({})
  }

  const saveEditing = () => {
    if (editingId && editValues) {
      updateBet(editingId, editValues)
      setEditingId(null)
      setEditValues({})
    }
  }

  const handleSettleBet = (id: string, won: boolean) => {
    settleBet(id, won)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'won': return <CheckCircle className="h-4 w-4 text-green-400" />
      case 'lost': return <XCircle className="h-4 w-4 text-red-400" />
      default: return <Clock className="h-4 w-4 text-yellow-400" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'won': return 'text-green-400 bg-green-500/20'
      case 'lost': return 'text-red-400 bg-red-500/20'  
      default: return 'text-yellow-400 bg-yellow-500/20'
    }
  }

  const formatOdds = (odds: number) => odds > 0 ? `+${odds}` : `${odds}`
  
  const calculatePotentialPayout = (betAmount: number, odds: number) => {
    if (odds > 0) {
      return betAmount * (odds / 100)
    } else {
      return betAmount * (100 / Math.abs(odds))
    }
  }

  const calculateStats = () => {
    const settledBets = bets.filter(bet => bet.status !== 'pending')
    const wonBets = bets.filter(bet => bet.status === 'won').length
    const lostBets = bets.filter(bet => bet.status === 'lost').length
    const totalWagered = settledBets.reduce((sum, bet) => sum + bet.bet_amount, 0)
    const totalReturned = settledBets.reduce((sum, bet) => sum + (bet.result_amount || 0), 0)
    const netProfit = totalReturned - totalWagered
    const winRate = settledBets.length > 0 ? (wonBets / settledBets.length) * 100 : 0
    const roi = totalWagered > 0 ? (netProfit / totalWagered) * 100 : 0

    return {
      totalBets: bets.length,
      wonBets,
      lostBets,
      pendingBets: bets.filter(bet => bet.status === 'pending').length,
      winRate: Math.round(winRate * 10) / 10,
      netProfit: Math.round(netProfit * 100) / 100,
      roi: Math.round(roi * 10) / 10,
      totalWagered: Math.round(totalWagered * 100) / 100
    }
  }

  const stats = calculateStats()
  const profitColor = stats.netProfit >= 0 ? 'text-green-400' : 'text-red-400'

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-black/40 backdrop-blur-sm rounded-lg border border-gray-700 p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{stats.totalBets}</div>
            <div className="text-sm text-gray-400">Total Bets</div>
          </div>
        </div>
        
        <div className="bg-black/40 backdrop-blur-sm rounded-lg border border-gray-700 p-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{stats.winRate}%</div>
            <div className="text-sm text-gray-400">Win Rate</div>
          </div>
        </div>
        
        <div className="bg-black/40 backdrop-blur-sm rounded-lg border border-gray-700 p-4">
          <div className="text-center">
            <div className={`text-2xl font-bold ${profitColor}`}>
              ${stats.netProfit >= 0 ? '+' : ''}${stats.netProfit}
            </div>
            <div className="text-sm text-gray-400">Net Profit</div>
          </div>
        </div>
        
        <div className="bg-black/40 backdrop-blur-sm rounded-lg border border-gray-700 p-4">
          <div className="text-center">
            <div className={`text-2xl font-bold ${profitColor}`}>
              {stats.roi >= 0 ? '+' : ''}{stats.roi}%
            </div>
            <div className="text-sm text-gray-400">ROI</div>
          </div>
        </div>
      </div>

      {/* Editable Bet Table */}
      <div className="bg-black/40 backdrop-blur-sm rounded-lg border border-gray-700">
        <div className="p-6 border-b border-gray-700">
          <h2 className="text-xl font-semibold text-white">Bet Tracking</h2>
          <p className="text-gray-400 text-sm">Click edit to modify bets, or settle completed fights</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left p-4 text-gray-300 font-medium">Fight</th>
                <th className="text-left p-4 text-gray-300 font-medium">Book & Odds</th>
                <th className="text-center p-4 text-gray-300 font-medium">Bet Amount</th>
                <th className="text-center p-4 text-gray-300 font-medium">EV Edge</th>
                <th className="text-center p-4 text-gray-300 font-medium">Potential</th>
                <th className="text-center p-4 text-gray-300 font-medium">Status</th>
                <th className="text-center p-4 text-gray-300 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {bets.map((bet, index) => (
                <tr key={bet.id} className={`border-b border-gray-800 hover:bg-white/5 ${
                  index % 2 === 0 ? 'bg-black/20' : ''
                }`}>
                  {/* Fight */}
                  <td className="p-4">
                    <div>
                      <div className="font-medium text-white">{bet.fighter}</div>
                      <div className="text-sm text-gray-400">vs {bet.opponent}</div>
                    </div>
                  </td>

                  {/* Book & Odds */}
                  <td className="p-4">
                    {editingId === bet.id ? (
                      <div className="space-y-2">
                        <input
                          type="text"
                          value={editValues.book || ''}
                          onChange={(e) => setEditValues(prev => ({ ...prev, book: e.target.value }))}
                          className="w-full bg-gray-800 text-white px-2 py-1 rounded text-sm"
                        />
                        <input
                          type="number"
                          value={editValues.odds || ''}
                          onChange={(e) => setEditValues(prev => ({ ...prev, odds: parseInt(e.target.value) || 0 }))}
                          className="w-full bg-gray-800 text-white px-2 py-1 rounded text-sm font-mono"
                          placeholder="Odds"
                        />
                      </div>
                    ) : (
                      <div>
                        <div className="text-white font-medium">{bet.book}</div>
                        <div className="text-sm text-gray-300 font-mono">{formatOdds(bet.odds)}</div>
                      </div>
                    )}
                  </td>

                  {/* Bet Amount */}
                  <td className="p-4 text-center">
                    {editingId === bet.id ? (
                      <div className="space-y-2">
                        <input
                          type="number"
                          step="0.01"
                          value={editValues.bet_amount || ''}
                          onChange={(e) => setEditValues(prev => ({ ...prev, bet_amount: parseFloat(e.target.value) || 0 }))}
                          className="w-20 bg-gray-800 text-white px-2 py-1 rounded text-sm text-center"
                        />
                        <div className="text-xs text-gray-400">
                          {((editValues.bet_amount || 0) / 10).toFixed(1)} units
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div className="text-white font-medium">${bet.bet_amount}</div>
                        <div className="text-sm text-gray-400">{bet.unit_size} units</div>
                      </div>
                    )}
                  </td>

                  {/* EV Edge */}
                  <td className="p-4 text-center">
                    <div className="text-green-400 font-medium">+{bet.ev_percentage}%</div>
                    <div className="text-sm text-gray-400">{bet.confidence_score}/100</div>
                  </td>

                  {/* Potential */}
                  <td className="p-4 text-center">
                    {bet.status === 'pending' ? (
                      <div>
                        <div className="text-white font-medium">
                          ${(bet.bet_amount + calculatePotentialPayout(bet.bet_amount, bet.odds)).toFixed(2)}
                        </div>
                        <div className="text-sm text-gray-400">
                          +${calculatePotentialPayout(bet.bet_amount, bet.odds).toFixed(2)}
                        </div>
                      </div>
                    ) : (
                      <div className={`font-medium ${bet.status === 'won' ? 'text-green-400' : 'text-red-400'}`}>
                        ${bet.result_amount?.toFixed(2) || '0.00'}
                      </div>
                    )}
                  </td>

                  {/* Status */}
                  <td className="p-4 text-center">
                    <div className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${getStatusColor(bet.status)}`}>
                      {getStatusIcon(bet.status)}
                      {bet.status.toUpperCase()}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="p-4 text-center">
                    <div className="flex items-center justify-center gap-2">
                      {editingId === bet.id ? (
                        <>
                          <button
                            onClick={saveEditing}
                            className="text-green-400 hover:text-green-300"
                            title="Save changes"
                          >
                            <Save className="h-4 w-4" />
                          </button>
                          <button
                            onClick={cancelEditing}
                            className="text-red-400 hover:text-red-300"
                            title="Cancel"
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => startEditing(bet)}
                            className="text-blue-400 hover:text-blue-300"
                            title="Edit bet"
                          >
                            <Edit2 className="h-4 w-4" />
                          </button>
                          
                          {bet.status === 'pending' && (
                            <>
                              <button
                                onClick={() => handleSettleBet(bet.id, true)}
                                className="text-green-400 hover:text-green-300"
                                title="Mark as won"
                              >
                                <CheckCircle className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleSettleBet(bet.id, false)}
                                className="text-red-400 hover:text-red-300"
                                title="Mark as lost"
                              >
                                <XCircle className="h-4 w-4" />
                              </button>
                            </>
                          )}
                          
                          <button
                            onClick={() => deleteBet(bet.id)}
                            className="text-gray-400 hover:text-red-400"
                            title="Delete bet"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {bets.length === 0 && (
          <div className="p-8 text-center">
            <div className="text-gray-400 mb-2">No bets tracked yet</div>
           <div className="text-gray-500 text-sm">Click &quot;Place Bet&quot; on +EV opportunities to get started</div>
          </div>
        )}
      </div>
    </div>
  )
}