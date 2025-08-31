import { Target, TrendingUp, AlertCircle, CheckCircle, Plus } from 'lucide-react'
import { useBetManager } from './BetManager'

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

interface EVOpportunitiesProps {
  opportunities: EVOpportunity[]
}

export default function EVOpportunities({ opportunities }: EVOpportunitiesProps) {
  const { addBet } = useBetManager()

  const getEVColor = (ev: number) => {
    if (ev >= 3.0) return 'from-green-600 to-green-700'
    if (ev >= 2.0) return 'from-green-500 to-green-600'
    if (ev >= 1.5) return 'from-blue-500 to-blue-600'
    if (ev >= 1.0) return 'from-yellow-500 to-yellow-600'
    return 'from-gray-500 to-gray-600'
  }

  const getEVIcon = (ev: number) => {
    if (ev >= 2.5) return <TrendingUp className="h-4 w-4" />
    if (ev >= 1.5) return <CheckCircle className="h-4 w-4" />
    return <AlertCircle className="h-4 w-4" />
  }

  const getRecommendationEmoji = (recommendation: string) => {
    if (recommendation.includes('🔥')) return '🔥'
    if (recommendation.includes('✅')) return '✅'
    if (recommendation.includes('📊')) return '📊'
    return '⚠️'
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 80) return 'text-green-400'
    if (score >= 60) return 'text-blue-400'
    if (score >= 40) return 'text-yellow-400'
    return 'text-gray-400'
  }

  const handlePlaceBet = (opp: EVOpportunity) => {
    console.log('🎯 Place bet clicked for:', opp.fighter, '@', opp.book)
    console.log('🔧 addBet function:', typeof addBet)
    console.log('📊 Full opportunity object:', opp)
    
    try {
      // Extract opponent from fight_info (e.g., "Jon Jones vs Tom Aspinall")
      const fightParts = opp.fight_info.split(' vs ')
      const opponent = fightParts.find(part => part.trim() !== opp.fighter)?.trim() || 'Unknown'
      
      console.log('👥 Fighter:', opp.fighter, 'vs Opponent:', opponent)
      
      // Get odds for this fighter/book combination (estimate based on EV calculation)
      const estimatedOdds = opp.sharp_consensus_prob > 50 ? -150 : 150
      
      const newBet = {
        fighter: opp.fighter,
        opponent: opponent,
        book: opp.book,
        odds: estimatedOdds,
        bet_amount: opp.kelly_dollars || 10,
        unit_size: opp.kelly_units || 1,
        ev_percentage: opp.ev_percentage,
        confidence_score: opp.confidence_score,
        kelly_recommended: opp.kelly_size || 1,
        fight_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 7 days from now
        notes: `Auto-added from ${opp.recommendation}`
      }
      
      console.log('💰 About to add bet:', newBet)
      addBet(newBet)
      console.log('✅ Bet added successfully!')
      
      // Visual feedback
      alert(`Added bet: ${opp.fighter} @ ${opp.book} for $${opp.kelly_dollars || 10}`)
      
    } catch (error) {
      console.error('❌ Error in handlePlaceBet:', error)
      alert('Error adding bet - check console for details')
    }
  }

  return (
    <div className="bg-black/40 backdrop-blur-sm rounded-lg border border-gray-700 p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <Target className="h-5 w-5 text-orange-500" />
          +EV Opportunities
        </h2>
        <div className="bg-orange-500/20 text-orange-400 px-3 py-1 rounded-full text-sm font-medium">
          {opportunities.length} Found
        </div>
      </div>

      {opportunities.length === 0 ? (
        <div className="text-center py-8">
          <Target className="h-12 w-12 text-gray-500 mx-auto mb-3" />
          <p className="text-gray-400 mb-2">No +EV opportunities found</p>
          <p className="text-gray-500 text-sm">Check back after odds update</p>
        </div>
      ) : (
        <div className="space-y-4">
          {opportunities.slice(0, 10).map((opp, index) => (
            <div 
              key={index} 
              className={`relative overflow-hidden rounded-lg bg-gradient-to-r ${getEVColor(opp.ev_percentage)} p-4`}
            >
              {/* Background overlay for better text readability */}
              <div className="absolute inset-0 bg-black/30"></div>
              
              <div className="relative">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    {getEVIcon(opp.ev_percentage)}
                    <span className="font-medium text-white">
                      {getRecommendationEmoji(opp.recommendation)} {opp.fighter}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-white">
                      +{opp.ev_percentage.toFixed(1)}%
                    </div>
                    <div className={`text-xs ${getConfidenceColor(opp.confidence_score)}`}>
                      {opp.confidence_score}/100
                    </div>
                  </div>
                </div>

                {/* Book info */}
                <div className="mb-3">
                  <div className="text-white/90 text-sm font-medium">@ {opp.book}</div>
                  <div className="text-white/70 text-xs">{opp.fight_info}</div>
                </div>

                {/* Probability comparison */}
                <div className="bg-black/30 rounded-lg p-3 mb-3">
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <div className="text-white/60 mb-1">Sharp Consensus</div>
                      <div className="text-white font-mono">{opp.sharp_consensus_prob.toFixed(1)}%</div>
                    </div>
                    <div>
                      <div className="text-white/60 mb-1">{opp.book} Price</div>
                      <div className="text-white font-mono">{opp.square_prob.toFixed(1)}%</div>
                    </div>
                  </div>
                </div>

                {/* Kelly Sizing */}
                {opp.kelly_size && (
                  <div className="bg-black/30 rounded-lg p-3 mb-2">
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <div className="text-white/60 mb-1">Kelly Size</div>
                        <div className="text-white font-mono">{opp.kelly_size}%</div>
                        <div className="text-white/40 text-xs">{opp.kelly_category}</div>
                      </div>
                      <div>
                        <div className="text-white/60 mb-1">Bet Amount</div>
                        <div className="text-white font-mono">${opp.kelly_dollars}</div>
                        <div className="text-white/40 text-xs">{opp.kelly_units} units</div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Recommendation + Place Bet Button */}
                <div className="flex items-center justify-between">
                  <div className="bg-white/20 rounded-full px-3 py-1 text-xs font-medium text-white">
                    {opp.recommendation.replace(/[🔥✅📊⚠️]/g, '').trim()}
                  </div>
                  <button
                    onClick={(e) => {
                      console.log('🖱️ Button clicked!')
                      e.preventDefault()
                      e.stopPropagation()
                      handlePlaceBet(opp)
                    }}
                    className="bg-white/20 hover:bg-white/30 rounded-full px-3 py-1 text-xs font-medium text-white flex items-center gap-1 transition-colors cursor-pointer"
                    type="button"
                  >
                    <Plus className="h-3 w-3" />
                    Place Bet
                  </button>
                </div>
              </div>
            </div>
          ))}

          {/* Show more indicator if there are more opportunities */}
          {opportunities.length > 10 && (
            <div className="text-center py-4">
              <button className="text-orange-400 hover:text-orange-300 text-sm font-medium">
                View {opportunities.length - 10} more opportunities →
              </button>
            </div>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-gray-700">
        <div className="text-xs text-gray-400 space-y-1">
          <div className="flex justify-between">
            <span>🔥 Strong Bet:</span>
            <span>&gt;2.5% EV</span>
          </div>
          <div className="flex justify-between">
            <span>✅ Good Bet:</span>
            <span>&gt;1.5% EV</span>
          </div>
          <div className="flex justify-between">
            <span>📊 Decent Bet:</span>
            <span>&gt;1.0% EV</span>
          </div>
        </div>
      </div>
    </div>
  )
}