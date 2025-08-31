import json
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import sqlite3

@dataclass
class KellyResult:
    recommended_percentage: float  # % of bankroll
    recommended_dollars: float     # Actual dollar amount
    unit_size: float              # In "units" (your $10 standard)
    risk_level: str
    kelly_category: str

@dataclass
class PlacedBet:
    id: int
    fighter: str
    opponent: str
    book: str
    odds: int
    bet_amount: float
    unit_size: float
    ev_percentage: float
    confidence_score: float
    kelly_recommended: float
    placed_date: datetime
    fight_date: datetime
    status: str  # 'pending', 'won', 'lost', 'cancelled'
    result_amount: Optional[float] = None
    settled_date: Optional[datetime] = None

class KellyCalculator:
    def __init__(self, bankroll: float = 1000.0, standard_unit: float = 10.0):
        self.bankroll = bankroll
        self.standard_unit = standard_unit
        self.strategy = 'half_kelly'  # Conservative balanced approach
        
        # Your book classifications
        self.sharp_books = ['Pinnacle', 'BetOnline', 'Circa Sports']
        self.target_books = ['DraftKings', 'Bet365', 'FanDuel']  # Books you can actually bet
        
        # Safety limits
        self.max_bet_percentage = 5.0  # Never bet more than 5% of bankroll
        self.min_bet_percentage = 0.5  # Don't bother with tiny edges
    
    def calculate_kelly_size(self, ev_percentage: float, 
                           sharp_probability: float, 
                           american_odds: int) -> KellyResult:
        """Calculate optimal bet size using Half-Kelly"""
        
        # Convert American odds to decimal
        if american_odds > 0:
            decimal_odds = (american_odds / 100) + 1
            payout_multiplier = american_odds / 100
        else:
            decimal_odds = (100 / abs(american_odds)) + 1  
            payout_multiplier = 100 / abs(american_odds)
        
        # Kelly formula: f* = (bp - q) / b
        b = payout_multiplier
        p = sharp_probability / 100  # Convert percentage to decimal
        q = 1 - p
        
        # Full Kelly percentage
        if b <= 0:  # Edge case
            full_kelly = 0
        else:
            full_kelly = (b * p - q) / b
        
        # Half Kelly for conservative approach
        half_kelly = full_kelly * 0.5
        
        # Convert to percentage of bankroll
        kelly_percentage = half_kelly * 100
        
        # Apply safety limits
        if kelly_percentage < self.min_bet_percentage:
            recommended_percentage = 0
            risk_level = "SKIP"
            kelly_category = "❌ TOO SMALL"
        elif kelly_percentage > self.max_bet_percentage:
            recommended_percentage = self.max_bet_percentage
            risk_level = "CAPPED"
            kelly_category = "⚠️ CAPPED"
        else:
            recommended_percentage = kelly_percentage
            
            # Categorize bet size
            if recommended_percentage >= 3.0:
                risk_level = "HIGH"
                kelly_category = "🔥 LARGE"
            elif recommended_percentage >= 2.0:
                risk_level = "MEDIUM" 
                kelly_category = "💪 MEDIUM"
            elif recommended_percentage >= 1.0:
                risk_level = "LOW"
                kelly_category = "📊 SMALL"
            else:
                risk_level = "MINIMAL"
                kelly_category = "🤏 TINY"
        
        # Calculate dollar amounts
        recommended_dollars = (recommended_percentage / 100) * self.bankroll
        unit_size = recommended_dollars / self.standard_unit
        
        return KellyResult(
            recommended_percentage=round(recommended_percentage, 2),
            recommended_dollars=round(recommended_dollars, 2),
            unit_size=round(unit_size, 2),
            risk_level=risk_level,
            kelly_category=kelly_category
        )
    
    def update_bankroll(self, new_bankroll: float):
        """Update bankroll after wins/losses"""
        self.bankroll = new_bankroll
        print(f"💰 Bankroll updated to ${new_bankroll:.2f}")

class BetTracker:
    def __init__(self, db_path: str = "../data/bet_tracker.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database for bet tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS placed_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fighter TEXT NOT NULL,
                opponent TEXT NOT NULL,
                book TEXT NOT NULL,
                odds INTEGER NOT NULL,
                bet_amount REAL NOT NULL,
                unit_size REAL NOT NULL,
                ev_percentage REAL NOT NULL,
                confidence_score REAL NOT NULL,
                kelly_recommended REAL NOT NULL,
                placed_date TEXT NOT NULL,
                fight_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                result_amount REAL,
                settled_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_bet(self, fighter: str, opponent: str, book: str, odds: int,
                bet_amount: float, unit_size: float, ev_percentage: float,
                confidence_score: float, kelly_recommended: float,
                fight_date: str) -> int:
        """Add a new bet to tracking"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO placed_bets 
            (fighter, opponent, book, odds, bet_amount, unit_size, ev_percentage,
             confidence_score, kelly_recommended, placed_date, fight_date, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (fighter, opponent, book, odds, bet_amount, unit_size, ev_percentage,
              confidence_score, kelly_recommended, datetime.now().isoformat(), fight_date))
        
        bet_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ Added bet: {fighter} ${bet_amount} @ {book}")
        return bet_id
    
    def settle_bet(self, bet_id: int, won: bool):
        """Mark bet as won/lost and calculate result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get bet details
        cursor.execute('SELECT * FROM placed_bets WHERE id = ?', (bet_id,))
        bet = cursor.fetchone()
        
        if not bet:
            print(f"❌ Bet ID {bet_id} not found")
            return
        
        bet_amount = bet[5]  # bet_amount column
        odds = bet[4]       # odds column
        
        if won:
            # Calculate payout
            if odds > 0:
                payout = bet_amount * (odds / 100)
            else:
                payout = bet_amount * (100 / abs(odds))
            
            result_amount = bet_amount + payout  # Original stake + winnings
            status = 'won'
            print(f"🎉 Bet won! Payout: ${result_amount:.2f}")
        else:
            result_amount = 0  # Lost the stake
            status = 'lost'
            print(f"😞 Bet lost. Lost ${bet_amount}")
        
        # Update database
        cursor.execute('''
            UPDATE placed_bets 
            SET status = ?, result_amount = ?, settled_date = ?
            WHERE id = ?
        ''', (status, result_amount, datetime.now().isoformat(), bet_id))
        
        conn.commit()
        conn.close()
    
    def get_betting_stats(self) -> Dict:
        """Get overall betting statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall stats
        cursor.execute('SELECT COUNT(*) FROM placed_bets')
        total_bets = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM placed_bets WHERE status = "won"')
        won_bets = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM placed_bets WHERE status = "lost"')  
        lost_bets = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM placed_bets WHERE status = "pending"')
        pending_bets = cursor.fetchone()[0]
        
        # Financial stats
        cursor.execute('SELECT SUM(bet_amount) FROM placed_bets')
        total_wagered = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(result_amount) FROM placed_bets WHERE status IN ("won", "lost")')
        total_returned = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(bet_amount) FROM placed_bets WHERE status IN ("won", "lost")')
        total_risked = cursor.fetchone()[0] or 0
        
        # Calculate profit/loss
        net_profit = total_returned - total_risked
        
        # Win rate
        win_rate = (won_bets / (won_bets + lost_bets)) * 100 if (won_bets + lost_bets) > 0 else 0
        
        # ROI
        roi = (net_profit / total_risked) * 100 if total_risked > 0 else 0
        
        conn.close()
        
        return {
            'total_bets': total_bets,
            'won_bets': won_bets,
            'lost_bets': lost_bets,
            'pending_bets': pending_bets,
            'win_rate': round(win_rate, 1),
            'total_wagered': round(total_wagered, 2),
            'net_profit': round(net_profit, 2),
            'roi': round(roi, 1),
            'avg_bet_size': round(total_wagered / total_bets, 2) if total_bets > 0 else 0
        }
    
    def get_recent_bets(self, limit: int = 20) -> List[Dict]:
        """Get recent bets with details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM placed_bets 
            ORDER BY placed_date DESC 
            LIMIT ?
        ''', (limit,))
        
        bets = cursor.fetchall()
        conn.close()
        
        # Convert to list of dictionaries
        bet_list = []
        for bet in bets:
            bet_dict = {
                'id': bet[0],
                'fighter': bet[1], 
                'opponent': bet[2],
                'book': bet[3],
                'odds': bet[4],
                'bet_amount': bet[5],
                'unit_size': bet[6],
                'ev_percentage': bet[7],
                'confidence_score': bet[8],
                'kelly_recommended': bet[9],
                'placed_date': bet[10],
                'fight_date': bet[11],
                'status': bet[12],
                'result_amount': bet[13],
                'settled_date': bet[14]
            }
            bet_list.append(bet_dict)
        
        return bet_list

def main():
    """Test the Kelly calculator and bet tracker"""
    
    # Initialize with your parameters
    kelly = KellyCalculator(bankroll=1000.0, standard_unit=10.0)
    tracker = BetTracker()
    
    # Test Kelly calculation with your Jon Jones example
    print("🧮 Testing Kelly Calculator:")
    print("-" * 40)
    
    kelly_result = kelly.calculate_kelly_size(
        ev_percentage=2.2,
        sharp_probability=57.5,
        american_odds=-135
    )
    
    print(f"EV: +2.2% | Sharp Probability: 57.5% | Odds: -135")
    print(f"Kelly Recommendation: {kelly_result.kelly_category}")
    print(f"Bet Size: {kelly_result.recommended_percentage}% (${kelly_result.recommended_dollars})")
    print(f"Unit Size: {kelly_result.unit_size} units")
    print(f"Risk Level: {kelly_result.risk_level}")
    
    # Test adding a bet
    print(f"\n📊 Adding sample bet to tracker:")
    bet_id = tracker.add_bet(
        fighter="Jon Jones",
        opponent="Tom Aspinall", 
        book="DraftKings",
        odds=-135,
        bet_amount=kelly_result.recommended_dollars,
        unit_size=kelly_result.unit_size,
        ev_percentage=2.2,
        confidence_score=68.1,
        kelly_recommended=kelly_result.recommended_percentage,
        fight_date="2024-11-16"
    )
    
    # Show current stats
    print(f"\n📈 Current Betting Stats:")
    stats = tracker.get_betting_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Show recent bets
    print(f"\n📋 Recent Bets:")
    recent = tracker.get_recent_bets(limit=5)
    for bet in recent:
        print(f"   {bet['fighter']} vs {bet['opponent']} | ${bet['bet_amount']} @ {bet['book']} | Status: {bet['status']}")

if __name__ == "__main__":
    main()