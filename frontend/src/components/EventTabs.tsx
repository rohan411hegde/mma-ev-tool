'use client';

import { useState, useEffect, useCallback } from 'react';
import { Calendar, Users } from 'lucide-react';

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

  const fetchEvents = useCallback(async () => {
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
        setError('No events found');
        setEvents([]);
      }
    } catch (error) {
      console.error('Failed to fetch events:', error);
      setError('Could not load events');
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [onEventSelect, selectedEventId]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const formatDate = (dateString: string) => {
    try {
      if (!dateString) return 'Unknown Date';
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Unknown Date';
      
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric'
      });
    } catch {
      return 'Unknown Date';
    }
  };

  if (loading) {
    return (
      <div className="w-full mb-6">
        <div className="flex items-center space-x-2 text-gray-400">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-500"></div>
          <span>Loading events...</span>
        </div>
      </div>
    );
  }

  if (error || events.length === 0) {
    return (
      <div className="w-full mb-6">
        <div className="bg-gray-800 rounded-lg p-6 text-center border border-gray-700">
          <Calendar className="w-8 h-8 text-gray-500 mx-auto mb-2" />
          <p className="text-gray-400">No events available</p>
          <p className="text-sm text-gray-500 mt-1">Check back after the next scrape</p>
          <button 
            onClick={fetchEvents}
            className="mt-3 text-orange-400 hover:text-orange-300 underline text-sm"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full mb-6">
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
      <div className="flex space-x-2 overflow-x-auto pb-2">
        {events.map((event) => {
          const isSelected = selectedEventId === event.event_id;
          
          return (
            <button
              key={event.event_id}
              onClick={() => onEventSelect(event.event_id)}
              className={`
                flex-shrink-0 px-4 py-3 rounded-lg border transition-all duration-200
                min-w-[180px] text-left
                ${isSelected
                  ? 'bg-orange-600 border-orange-500 text-white shadow-lg' 
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:bg-gray-700 hover:border-gray-600'
                }
              `}
            >
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