'use client';

interface ApiFight {
  fighter1: string;
  fighter2: string;
  event_name: string;
  event_date: string;
  weight_class: string;
  odds_data: Array<{
    fighter_name: string;
    odds: number;
    book: string;
  }>;
  scraped_at?: string;
}

interface EventCardProps {
  fights: ApiFight[];
  eventName: string;
  eventDate: string;
}

export default function EventCard({ fights, eventName, eventDate }: EventCardProps) {
  if (!fights || fights.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <p className="text-gray-400 text-center">No fights available for this event</p>
      </div>
    );
  }

  const formatOdds = (odds: number) => {
    return odds > 0 ? `+${odds}` : `${odds}`;
  };

  const getOddsColor = (odds: number) => {
    return odds > 0 ? 'text-green-400' : 'text-red-400';
  };

  return (
    <div className="space-y-4">
      {fights.map((fight, index) => (
        <div key={index} className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          {/* Fight Header */}
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">
                {fight.fighter1} vs {fight.fighter2}
              </h3>
              <p className="text-sm text-gray-400">
                {fight.weight_class} • {eventName}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">
                {new Date(eventDate).toLocaleDateString()}
              </p>
              {fight.scraped_at && (
                <p className="text-xs text-gray-600">
                  Updated: {new Date(fight.scraped_at).toLocaleTimeString()}
                </p>
              )}
            </div>
          </div>

          {/* Odds Section */}
          {fight.odds_data && fight.odds_data.length > 0 && (
            <div className="border-t border-gray-700 pt-4">
              <h4 className="text-sm font-medium text-gray-300 mb-3">Betting Odds</h4>
              
              {/* Group odds by fighter */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Fighter 1 Odds */}
                <div>
                  <h5 className="text-sm font-medium text-white mb-2">{fight.fighter1}</h5>
                  <div className="space-y-1">
                    {fight.odds_data
                      .filter(odds => odds.fighter_name === fight.fighter1)
                      .map((odds, oddsIndex) => (
                        <div key={oddsIndex} className="flex justify-between items-center py-1">
                          <span className="text-sm text-gray-400">{odds.book}</span>
                          <span className={`text-sm font-medium ${getOddsColor(odds.odds)}`}>
                            {formatOdds(odds.odds)}
                          </span>
                        </div>
                      ))}
                  </div>
                </div>

                {/* Fighter 2 Odds */}
                <div>
                  <h5 className="text-sm font-medium text-white mb-2">{fight.fighter2}</h5>
                  <div className="space-y-1">
                    {fight.odds_data
                      .filter(odds => odds.fighter_name === fight.fighter2)
                      .map((odds, oddsIndex) => (
                        <div key={oddsIndex} className="flex justify-between items-center py-1">
                          <span className="text-sm text-gray-400">{odds.book}</span>
                          <span className={`text-sm font-medium ${getOddsColor(odds.odds)}`}>
                            {formatOdds(odds.odds)}
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              </div>

              {/* Summary */}
              <div className="mt-4 pt-3 border-t border-gray-700">
                <div className="flex justify-between text-xs text-gray-500">
                  <span>Total Sportsbooks: {new Set(fight.odds_data.map(odds => odds.book)).size}</span>
                  <span>Total Odds: {fight.odds_data.length}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}