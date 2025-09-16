'use client';

import { useState, useEffect } from 'react';
import { Target, TrendingUp, AlertCircle, RefreshCw } from 'lucide-react';

interface EVOpportunity {
  fighter: string;
  book: string;
  ev_percentage: number;
  confidence_score: number;
  sharp_consensus_prob: number;
  square_prob: number;
  recommendation: string;
  fight_info: string;
  kelly_size?: number;
  kelly_dollars?: number;
  kelly_units?: number;
  kelly_category?: string;
}

interface EVOpportunitiesProps {
  eventId?: string;
}

export default function EVOpportunities({ eventId }: EVOpportunitiesProps) {
  const [opportunities, setOpportunities] = useState<EVOpportunity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  useEffect(() => {
    if (eventId) {
      fetchEVOpportunities();
    } else {
      setOpportunities([]);
      setError(null);
    }
  }, [eventId]);

  const fetchEVOpportunities = async () => {
    if (!eventId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `https://mma-ev-tool.onrender.com/api/events/${eventId}/ev-opportunities`
      );
      const result = await response.json();

      if (result.success) {
        setOpportunities(result.data || []);
        setLastUpdated(new Date().toISOString());
      } else {
        setError(result.error || 'Failed to load EV opportunities');
        setOpportunities([]);
      }
    } catch (error) {
      console.error('Failed to fetch EV opportunities:', error);
      setError('Network error - could not load opportunities');
      setOpportunities([]);
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationStyle = (recommendation: string) => {
    switch (recommendation.toLowerCase()) {
      case 'strong bet':
        return 'bg-orange-900/50 text-orange-300 border-orange-700';
      case 'good bet':
        return 'bg-green-900/50 text-green-300 border-green-700';
      case 'decent bet':
        return 'bg-blue-900/50 text-blue-300 border-blue-700';
      default:
        return 'bg-gray-700/50 text-gray-300 border-gray-600';
    }
  };

  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation.toLowerCase()) {
      case 'strong bet':
        return '🔥';
      case 'good bet':
        return '✅';
      case 'decent bet':
        return '📈';
      default:
        return '📊';
    }
  };

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
  };

  const strongBets = opportunities.filter(opp => opp.ev_percentage >= 2.5);
  const goodBets = opportunities.filter(opp => opp.ev_percentage >= 1.5 && opp.ev_percentage < 2.5);
  const decentBets = opportunities.filter(opp => opp.ev_percentage >= 1.0 && opp.ev_percentage < 1.5);

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white flex items-center">
            <Target className="w-5 h-5 mr-2 text-orange-500" />
            +EV Opportunities
          </h3>
          {opportunities.length > 0 && (
            <span className="bg-orange-900/50 text-orange-300 px-2 py-1 rounded-full text-sm border border-orange-700">
              {opportunities.length} Found
            </span>
          )}
        </div>
        
        {lastUpdated && (
          <p className="text-xs text-gray-500 mt-1">
            Last updated: {new Date(lastUpdated).toLocaleTimeString()}
          </p>
        )}
      </div>

      {/* Content */}
      <div className="p-4">
        {loading && (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 text-orange-500 animate-spin mr-2" />
            <span className="text-gray-400">Calculating opportunities...</span>
          </div>
        )}

        {error && !loading && (
          <div className="text-center py-8">
            <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
            <p className="text-red-300 text-sm mb-3">{error}</p>
            <button
              onClick={fetchEVOpportunities}
              className="text-red-400 hover:text-red-300 underline text-sm"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && opportunities.length === 0 && (
          <div className="text-center py-8">
            <Target className="w-12 h-12 text-gray-500 mx-auto mb-4" />
            <p className="text-gray-400 mb-2">No +EV opportunities found</p>
            <p className="text-sm text-gray-500">Check back after odds update</p>
          </div>
        )}

        {!loading && !error && opportunities.length > 0 && (
          <div className="space-y-4">
            {/* Opportunities List */}
            <div className="space-y-3">
              {opportunities
                .sort((a, b) => b.ev_percentage - a.ev_percentage)
                .map((opportunity, index) => (
                  <div
                    key={index}
                    className="bg-gray-700/50 rounded-lg p-3 border border-gray-600 hover:border-gray-500 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-sm font-medium text-white">
                            {opportunity.fighter}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full border ${getRecommendationStyle(opportunity.recommendation)}`}>
                            {getRecommendationIcon(opportunity.recommendation)} {opportunity.recommendation}
                          </span>
                        </div>
                        <p className="text-xs text-gray-400 mb-1">
                          {opportunity.fight_info}
                        </p>
                        <p className="text-xs text-gray-500">
                          Book: {opportunity.book}
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-lg font-bold text-green-400">
                          {formatPercentage(opportunity.ev_percentage)}
                        </div>
                        <div className="text-xs text-gray-500">EV</div>
                      </div>
                    </div>

                    {/* Additional Details */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-gray-500">Sharp Prob:</span>
                        <span className="text-gray-300 ml-1">
                          {(opportunity.sharp_consensus_prob * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div>
                        <span className="text-gray-500">Square Prob:</span>
                        <span className="text-gray-300 ml-1">
                          {(opportunity.square_prob * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    {/* Kelly Sizing if available */}
                    {opportunity.kelly_size && (
                      <div className="mt-2 pt-2 border-t border-gray-600">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">Kelly Size:</span>
                          <span className="text-blue-300 font-medium">
                            {(opportunity.kelly_size * 100).toFixed(1)}%
                          </span>
                        </div>
                        {opportunity.kelly_category && (
                          <div className="flex items-center justify-between text-xs mt-1">
                            <span className="text-gray-500">Risk Level:</span>
                            <span className={`
                              font-medium
                              ${opportunity.kelly_category === 'Large' ? 'text-red-400' : 
                                opportunity.kelly_category === 'Medium' ? 'text-yellow-400' : 
                                'text-green-400'}
                            `}>
                              {opportunity.kelly_category}
                            </span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
            </div>

            {/* Summary Stats */}
            <div className="pt-4 border-t border-gray-700">
              <h4 className="text-sm font-medium text-gray-300 mb-3">Bet Quality Breakdown</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center text-orange-300">
                    🔥 Strong Bet:
                  </span>
                  <span className="text-gray-400">
                    {strongBets.length} (>2.5% EV)
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center text-green-300">
                    ✅ Good Bet:
                  </span>
                  <span className="text-gray-400">
                    {goodBets.length} (>1.5% EV)
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center text-blue-300">
                    📈 Decent Bet:
                  </span>
                  <span className="text-gray-400">
                    {decentBets.length} (>1.0% EV)
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Refresh Button */}
        {eventId && !loading && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <button
              onClick={fetchEVOpportunities}
              className="w-full flex items-center justify-center py-2 text-sm text-gray-400 hover:text-gray-300 transition-colors"
            >
              <RefreshCw className="w-4 h-4 mr-1" />
              Refresh Opportunities
            </button>
          </div>
        )}
      </div>
    </div>
  );
}