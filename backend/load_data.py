from flask import Flask, jsonify
from flask_cors import CORS
import json
import os
import glob
from datetime import datetime

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        'message': 'MMA EV Tool API',
        'version': '2.0',
        'endpoints': [
            '/api/fights',
            '/api/events', 
            '/api/events/<event_id>/fights',
            '/api/ev-opportunities',
            '/api/events/<event_id>/ev-opportunities'
        ]
    })

@app.route('/api/events', methods=['GET'])
def get_events_list():
    """Get list of all available events"""
    try:
        events_file = os.path.join('data', 'events_list.json')
        
        if not os.path.exists(events_file):
            return jsonify({
                'success': False, 
                'error': 'No events found',
                'data': []
            })
        
        with open(events_file, 'r') as f:
            events = json.load(f)
        
        return jsonify({
            'success': True, 
            'data': events,
            'count': len(events)
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Failed to load events: {str(e)}',
            'data': []
        })

@app.route('/api/events/<event_id>/fights', methods=['GET'])
def get_event_fights(event_id):
    """Get fights for specific event"""
    try:
        # Find the event file(s) for this event_id
        pattern = os.path.join('data', f'event_{event_id}_*.json')
        event_files = glob.glob(pattern)
        
        if not event_files:
            return jsonify({
                'success': False, 
                'error': f'Event {event_id} not found'
            })
        
        # Get the most recent file for this event (highest timestamp)
        latest_file = sorted(event_files)[-1]
        
        with open(latest_file, 'r') as f:
            event_data = json.load(f)
        
        return jsonify({
            'success': True, 
            'data': event_data,
            'file_loaded': os.path.basename(latest_file)
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Failed to load event data: {str(e)}'
        })

@app.route('/api/events/<event_id>/ev-opportunities', methods=['GET'])
def get_event_ev_opportunities(event_id):
    """Get EV opportunities for specific event"""
    try:
        # First get the event data
        pattern = os.path.join('data', f'event_{event_id}_*.json')
        event_files = glob.glob(pattern)
        
        if not event_files:
            return jsonify({
                'success': False, 
                'error': f'Event {event_id} not found'
            })
        
        latest_file = sorted(event_files)[-1]
        
        with open(latest_file, 'r') as f:
            event_data = json.load(f)
        
        # Calculate EV opportunities for this event
        from ev_calculator import calculate_ev_opportunities
        
        fights = event_data.get('fights', [])
        ev_opportunities = calculate_ev_opportunities(fights)
        
        return jsonify({
            'success': True, 
            'data': ev_opportunities,
            'event_id': event_id,
            'fights_analyzed': len(fights)
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Failed to calculate EV opportunities: {str(e)}',
            'data': []
        })

# Backward compatibility endpoints

@app.route('/api/fights', methods=['GET'])
def get_latest_fights():
    """Get fights for most recent event (backward compatibility)"""
    try:
        # Try to get from events list first
        events_file = os.path.join('data', 'events_list.json')
        
        if os.path.exists(events_file):
            with open(events_file, 'r') as f:
                events = json.load(f)
            
            if events:
                # Get the most recent event
                latest_event = events[0]
                return get_event_fights(latest_event['event_id'])
        
        # Fallback to old fights.json file
        fights_file = os.path.join('data', 'fights.json')
        
        if not os.path.exists(fights_file):
            return jsonify({
                'success': False, 
                'error': 'No fight data available'
            })
        
        with open(fights_file, 'r') as f:
            fights = json.load(f)
        
        return jsonify({
            'success': True, 
            'data': fights,
            'source': 'legacy_fights_file'
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Failed to load fights: {str(e)}'
        })

@app.route('/api/ev-opportunities', methods=['GET'])
def get_latest_ev_opportunities():
    """Get EV opportunities for most recent event (backward compatibility)"""
    try:
        # Try to get from events list first
        events_file = os.path.join('data', 'events_list.json')
        
        if os.path.exists(events_file):
            with open(events_file, 'r') as f:
                events = json.load(f)
            
            if events:
                # Get the most recent event
                latest_event = events[0]
                return get_event_ev_opportunities(latest_event['event_id'])
        
        # Fallback to calculating from fights.json
        fights_file = os.path.join('data', 'fights.json')
        
        if not os.path.exists(fights_file):
            return jsonify({
                'success': False, 
                'error': 'No fight data available for EV calculation',
                'data': []
            })
        
        with open(fights_file, 'r') as f:
            fights = json.load(f)
        
        from ev_calculator import calculate_ev_opportunities
        ev_opportunities = calculate_ev_opportunities(fights)
        
        return jsonify({
            'success': True, 
            'data': ev_opportunities,
            'source': 'legacy_calculation'
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Failed to calculate EV opportunities: {str(e)}',
            'data': []
        })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics across all events"""
    try:
        events_file = os.path.join('data', 'events_list.json')
        
        if not os.path.exists(events_file):
            return jsonify({
                'success': True,
                'data': {
                    'total_events': 0,
                    'total_fights': 0,
                    'total_opportunities': 0,
                    'avg_ev_edge': 0.0
                }
            })
        
        with open(events_file, 'r') as f:
            events = json.load(f)
        
        total_events = len(events)
        total_fights = sum(event.get('fights_count', 0) for event in events)
        
        # Calculate total opportunities across all events
        total_opportunities = 0
        total_ev = 0.0
        ev_count = 0
        
        for event in events:
            try:
                ev_response = get_event_ev_opportunities(event['event_id'])
                if ev_response.json.get('success'):
                    opportunities = ev_response.json.get('data', [])
                    total_opportunities += len(opportunities)
                    
                    for opp in opportunities:
                        if 'ev_percentage' in opp:
                            total_ev += opp['ev_percentage']
                            ev_count += 1
            except:
                continue
        
        avg_ev_edge = (total_ev / ev_count) if ev_count > 0 else 0.0
        
        return jsonify({
            'success': True,
            'data': {
                'total_events': total_events,
                'total_fights': total_fights,
                'total_opportunities': total_opportunities,
                'avg_ev_edge': round(avg_ev_edge, 2)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to calculate stats: {str(e)}',
            'data': {
                'total_events': 0,
                'total_fights': 0,
                'total_opportunities': 0,
                'avg_ev_edge': 0.0
            }
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)