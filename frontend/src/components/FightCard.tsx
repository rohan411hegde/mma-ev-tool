import { Calendar, Users, Weight } from 'lucide-react'

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

interface FightCardProps {
  fight: Fight
}

export default function FightCard({ fight }: FightCardProps) {
  // The odds are already organized by book in the new format
  const completeBooks = fight.odds.sort((a, b) => a.book.localeCompare(b.book))

  const formatOdds = (odds: number) => odds > 0 ? `+${odds}` : `${odds}`
  
  const getBookTypeColor = (book: string) => {
    const sharpBooks = ['Pinnacle', 'BetOnline', 'Circa Sports']
    return sharpBooks.includes(book) ? 'text-green-400' : 'text-blue-400'
  }

  const getBookTypeBadge = (book: string) => {
    const sharpBooks = ['Pinnacle', 'BetOnline', 'Circa Sports']
    return sharpBooks.includes(book) ? (
      <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">Sharp</span>
    ) : (
      <span className="text-xs bg-blue-500/20 text-blue-400 px-2 py-1 rounded">Square</span>
    )
  }

  return (
    <div className="bg-black/40 backdrop-blur-sm rounded-lg border border-gray-700 overflow-hidden">
      {/* Card Header */}
      <div className="bg-gradient-to-r from-orange-900/30 to-red-900/30 p-6 border-b border-gray-700">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-xl font-bold text-white mb-1">{fight.event_name}</h3>
            <div className="flex items-center gap-4 text-gray-300 text-sm">
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {new Date(fight.event_date).toLocaleDateString()}
              </div>
              <div className="flex items-center gap-1">
                <Weight className="h-4 w-4" />
                {fight.weight_class}
              </div>
            </div>
          </div>
        </div>

        {/* Fighter Matchup */}
        <div className="grid grid-cols-3 items-center gap-4">
          <div className="text-center">
            <div className="bg-black/30 rounded-lg p-4 border border-gray-600">
              <h4 className="text-lg font-semibold text-white mb-1">{fight.fighter1}</h4>
              <div className="text-gray-300 text-sm">Fighter 1</div>
            </div>
          </div>
          
          <div className="text-center">
            <div className="bg-orange-500/20 rounded-full w-12 h-12 flex items-center justify-center mx-auto border-2 border-orange-500">
              <Users className="h-5 w-5 text-orange-400" />
            </div>
            <div className="text-gray-300 text-xs mt-2">VS</div>
          </div>
          
          <div className="text-center">
            <div className="bg-black/30 rounded-lg p-4 border border-gray-600">
              <h4 className="text-lg font-semibold text-white mb-1">{fight.fighter2}</h4>
              <div className="text-gray-300 text-sm">Fighter 2</div>
            </div>
          </div>
        </div>
      </div>

      {/* Odds Table */}
      <div className="p-6">
        <h5 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          📊 Current Odds
        </h5>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 text-gray-300 font-medium">Sportsbook</th>
                <th className="text-center py-3 text-gray-300 font-medium">{fight.fighter1}</th>
                <th className="text-center py-3 text-gray-300 font-medium">{fight.fighter2}</th>
                <th className="text-center py-3 text-gray-300 font-medium">Type</th>
              </tr>
            </thead>
            <tbody>
              {completeBooks.map((odds, index) => (
                <tr 
                  key={odds.book} 
                  className={`border-b border-gray-800 hover:bg-white/5 transition-colors ${
                    index % 2 === 0 ? 'bg-black/20' : ''
                  }`}
                >
                  <td className="py-3">
                    <span className={`font-medium ${getBookTypeColor(odds.book)}`}>
                      {odds.book}
                    </span>
                  </td>
                  <td className="text-center py-3">
                    <span className="bg-gray-800 px-3 py-1 rounded text-white font-mono">
                      {formatOdds(odds.fighter1_odds)}
                    </span>
                  </td>
                  <td className="text-center py-3">
                    <span className="bg-gray-800 px-3 py-1 rounded text-white font-mono">
                      {formatOdds(odds.fighter2_odds)}
                    </span>
                  </td>
                  <td className="text-center py-3">
                    {getBookTypeBadge(odds.book)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Footer Info */}
        <div className="mt-4 text-xs text-gray-400 flex justify-between items-center">
          <span>📈 Sharp books provide market consensus</span>
          <span>Updated: {new Date(fight.scraped_at).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}</span>
        </div>
      </div>
    </div>
  )
}