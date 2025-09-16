'use client';

import { useState, useEffect } from 'react';
import { Calendar, TrendingUp, Users } from 'lucide-react';

interface Event {
  event_id: string;
  event_name: string;
  event_date: string;
  fights_count: number;
  last_updated: string;
  url?: string;
}

interface EventTabsProps {
  onEventSelect: (eventId: string) => void;
  selectedEventId?: string;
}

export default function EventTabs({ onEventSelect, selectedEventId }: EventTabsProps) {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('https://mma-ev-tool.onrender.com/api/events');
      const result = await response.json();
      
      if (result.success && result.data && Array.isArray(result.data)) {
        setEvents(result.data);
        // Auto-select first event if none selected and events exist
        if (result.data.length > 0 && !selectedEventId) {
          onEventSelect(result.data[0].event_id);
        }
      } else {
        setError(result.error || 'Failed to load events');
        setEvents([]);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
      setError('Network error - could not load events');
      setEvents([]);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      if (!dateString) return 'Unknown Date';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Unknown Date';
      
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return 'Unknown Date';
    }
  };

  const isUpcoming = (dateString: string) => {
    try {
      if (!dateString) return false;
      const eventDate = new Date(dateString);
      const now = new Date();
      return eventDate > now;
    } catch {
      return false;
    }
  };

  if (loading) {
    return (
      <div className="w-full">
        <div className="flex items-center space-x-2 text-gray-400">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-500"></div>
          <span>Loading events...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full">
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-4 text-red-300">
          <p className="text-sm">{error}</p>
          <button 
            onClick={fetchEvents}
            className="mt-2 text-xs text-red-400 hover:text-red-300 underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  if (!events || events.length === 0) {
    return (
      <div className="w-full">
        <div className="bg-gray-800 rounded-lg p-6 text-center">
          <Calendar className="w-8 h-8 text-gray-500 mx-auto mb-2" />
          <p className="text-gray-400">No events available</p>
          <p className="text-sm text-gray-500 mt-1">Check back after the next scrape</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full">
      {/* Section Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white flex items-center">
          <Calendar className="w-5 h-5 mr-2 text-orange-500" />
          Fight Events
        </h2>
        <div className="text-sm text-gray-400">
          {events.length} event{events.length !== 1 ? 's' : ''} available
        </div>
      </div>

      {/* Event Tabs */}
      <div className="flex space-x-2 overflow-x-auto pb-2 scrollbar-hide">
        {events.map((event, index) => {
          if (!event || !event.event_id) return null;
          
          const upcoming = isUpcoming(event.event_date);
          const isSelected = selectedEventId === event.event_id;
          
          return (
            <button
              key={event.event_id}
              onClick={() => onEventSelect(event.event_id)}
              className={`
                flex-shrink-0 relative px-4 py-3 rounded-lg border transition-all duration-200
                min-w-[200px] text-left
                ${isSelected
                  ? 'bg-orange-600 border-orange-500 text-white shadow-lg' 
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700 hover:border-gray-600'
                }
              `}
            >
              {/* Event Badge */}
              {index === 0 && upcoming && (
                <div className="absolute -top-1 -right-1 bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">
                  Latest
                </div>
              )}
              
              <div className="space-y-1">
                {/* Event Name */}
                <div className={`font-medium text-sm truncate ${isSelected ? 'text-white' : 'text-gray-200'}`}>
                  {event.event_name || 'Unknown Event'}
                </div>
                
                {/* Event Details */}
                <div className={`flex items-center space-x-3 text-xs ${isSelected ? 'text-orange-100' : 'text-gray-400'}`}>
                  <span className="flex items-center">
                    <Calendar className="w-3 h-3 mr-1" />
                    {formatDate(event.event_date)}
                  </span>
                  <span className="flex items-center">
                    <Users className="w-3 h-3 mr-1" />
                    {event.fights_count || 0} fights
                  </span>
                </div>
                
                {/* Status Indicator */}
                <div className="flex items-center justify-between">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    upcoming 
                      ? 'bg-green-900/50 text-green-300 border border-green-700'
                      : 'bg-gray-700/50 text-gray-400 border border-gray-600'
                  }`}>
                    {upcoming ? 'Upcoming' : 'Past'}
                  </span>
                  
                  {isSelected && (
                    <TrendingUp className="w-3 h-3 text-orange-300" />
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Mobile scroll hint */}
      <div className="md:hidden mt-2 text-xs text-gray-500 text-center">
        ← Scroll to see more events →
      </div>
    </div>
  );
}