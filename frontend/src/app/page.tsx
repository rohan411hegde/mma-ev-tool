'use client';

import { useState, useEffect } from 'react';
import EventTabs from '@/components/EventTabs';
import EventCard from '@/components/EventCard';
import EVOpportunities from '@/components/EVOpportunities';
import { Target, TrendingUp, BarChart3, Calendar } from 'lucide-react';

// Use a generic type to avoid conflicts with EventCard's Fight interface
interface EventData {
  event_id: string;
  event_name: string;
  event_date: string;
  fights: any[]; // Use any[] to avoid type conflicts with EventCard
  fights_count: number;
  scraped_at: string;
  url?: string;
}

export default function Home() {
  const [selectedEventId, setSelectedEventId] = useState<string>('');
  const [eventData, setEventData] = useState<EventData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedEventId) {
      fetchEventData(selectedEventId);
    }
  }, [selectedEventId]);

  const fetchEventData = async (eventId: string) => {
    if (!eventId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`https://mma-ev-tool.onrender.com/api/events/${eventId}/fights`);
      const result = await response.json();
      
      if (result.success && result.data) {
        setEventData(result.data);
      } else {
        setError(result.error || 'Failed to load event data');
        setEventData(null);
      }
    } catch (error) {
      console.error('Failed to fetch event data:', error);
      setError('Network error - could not load event data');
      setEventData(null);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', { 
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return 'Unknown Date';
    }
  };

  const getSportsbooksCount = (fights: any[]) => {
    const books = new Set<string>();
    fights.forEach(fight => {
      if (fight.odds_data && Array.isArray(fight.odds_data)) {
        fight.odds_data.forEach((odds: any) => {
          if (odds && odds.book) {
            books.add(odds.book);
          }
        });
      }
    });
    return books.size;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            MMA Expected Value Tool
          </h1>
          <p className="text-gray-400">
            Find profitable betting opportunities using sharp vs square betting analysis
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Opportunities</p>
                <p className="text-2xl font-bold text-white">0</p>
              </div>
              <Target className="w-8 h-8 text-orange-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Strong Bets</p>
                <p className="text-2xl font-bold text-green-400">0</p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Avg EV Edge</p>
                <p className="text-2xl font-bold text-blue-400">+0.0%</p>
              </div>
              <BarChart3 className="w-8 h-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Active Events</p>
                <p className="text-2xl font-bold text-purple-400">1</p>
              </div>
              <Calendar className="w-8 h-8 text-purple-500" />
            </div>
          </div>
        </div>

        {/* Event Tabs */}
        <EventTabs 
          onEventSelect={setSelectedEventId}
          selectedEventId={selectedEventId}
        />

        {/* Loading State */}
        {loading && (
          <div className="mt-8 text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading event data...</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="mt-8">
            <div className="bg-red-900/20 border border-red-700 rounded-lg p-6 text-center">
              <p className="text-red-300 mb-2">{error}</p>
              <button 
                onClick={() => selectedEventId && fetchEventData(selectedEventId)}
                className="text-red-400 hover:text-red-300 underline text-sm"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {/* Event Data Display */}
        {eventData && !loading && !error && (
          <div className="mt-8">
            {/* Selected Event Info Card */}
            <div className="bg-gray-800 rounded-lg p-6 mb-6 border border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-orange-600 rounded-lg flex items-center justify-center">
                    <Calendar className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-white">
                      {eventData.event_name}
                    </h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-400 mt-1">
                      <span>📅 {formatDate(eventData.event_date)}</span>
                      <span>🥊 {eventData.fights.length} Fights</span>
                      <span>📊 {getSportsbooksCount(eventData.fights)} Sportsbooks</span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-white">
                    {eventData.fights.length}
                  </div>
                  <div className="text-sm text-gray-400">Fights</div>
                  <div className="text-xs text-gray-500 mt-1">
                    Updated: {new Date(eventData.scraped_at).toLocaleTimeString()}
                  </div>
                </div>
              </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Fights List */}
              <div className="lg:col-span-2 space-y-4">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Fight Card ({eventData.fights.length} fights)
                </h3>
                
                {eventData.fights.length === 0 ? (
                  <div className="bg-gray-800 rounded-lg p-8 text-center border border-gray-700">
                    <p className="text-gray-400">No fights found for this event</p>
                  </div>
                ) : (
                  <EventCard 
                    fights={eventData.fights}
                    eventName={eventData.event_name}
                    eventDate={eventData.event_date}
                  />
                )}
              </div>
              
              {/* EV Opportunities Sidebar */}
              <div className="lg:col-span-1">
                <EVOpportunities eventId={selectedEventId} />
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!eventData && !loading && !error && (
          <div className="mt-8">
            <div className="bg-gray-800 rounded-lg p-8 text-center border border-gray-700">
              <Calendar className="w-12 h-12 text-gray-500 mx-auto mb-4" />
              <p className="text-gray-400 mb-2">No event data available</p>
              <p className="text-sm text-gray-500">
                Select an event from the tabs above to view fight data
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}