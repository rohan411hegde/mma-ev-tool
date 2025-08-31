import json
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict
from scraper import Fight, FighterOdds

@dataclass
class KellyResult:
    recommended_percentage: float  # % of bankroll
    recommended_dollars: float     # Actual dollar amount
    unit_size: float              # In "units" (your $10 standard)
    risk_level: str
    kelly_category: str

@dataclass
class EVResult:
    fighter: str
    book: str
    ev_percentage: float
    confidence_score: float
    sharp_consensus_prob: float
    square_prob: float
    recommendation: str
    fight_info: str
    # Kelly sizing fields
    kelly_size: float = 0.0
    kelly_dollars: float = 0.0
    kelly_units: float = 0.0
    kelly_category: str = ""

class KellyCalculator:
    def __init__(self, bankroll: float = 1000.0, standard_unit: float = 10.0):
        self.bankroll = bankroll
        self.standard_unit = standard_unit
        self.strategy = 'half_kelly'  # Conservative balanced approach
        
        # Safety limits
        self.max_bet_percentage = 10.0  # Never bet more than 10% of bankroll
        self.min_bet_percentage = 0.1  # Don't bother with tiny edges
    
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

class EVCalculator:
    def __init__(self):
        # Updated book classifications based on your preferences
        self.sharp_books = ['Pinnacle', 'BetOnline', 'Circa Sports']
        self.square_books = ['DraftKings', 'Bet365', 'FanDuel']  # Books you can actually bet on
        
        # EV thresholds
        self.ev_thresholds = {
            'conservative': 2.0,
            'moderate': 1.0,
            'aggressive': 0.5
        }
        
        # Initialize Kelly calculator with your bankroll
        self.kelly_calc = KellyCalculator(bankroll=1000.0, standard_unit=10.0)
    
    def odds_to_implied_prob(self, american_odds: int) -> float:
        """Convert American odds to implied probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return -american_odds / (-american_odds + 100)
    
    def remove_vig(self, fighter1_odds: int, fighter2_odds: int) -> Tuple[float, float]:
        """Remove bookmaker margin to get true probabilities (Method 3)"""
        prob1 = self.odds_to_implied_prob(fighter1_odds)
        prob2 = self.odds_to_implied_prob(fighter2_odds)
        
        total_prob = prob1 + prob2  # Should be > 1.0 due to vig
        
        if total_prob <= 1.0:
            # Edge case: no vig or negative vig (arbitrage opportunity!)
            return prob1, prob2
        
        # Remove vig proportionally
        true_prob1 = prob1 / total_prob
        true_prob2 = prob2 / total_prob
        
        return true_prob1, true_prob2
    
    def get_book_odds_for_fight(self, fight: Fight) -> Dict[str, Dict[str, int]]:
        """Organize odds by book for a specific fight"""
        book_odds = {}
        
        for odds in fight.odds_data:
            if odds.book not in book_odds:
                book_odds[odds.book] = {}
            book_odds[odds.book][odds.fighter_name] = odds.odds
        
        # Only return books that have odds for both fighters
        complete_books = {}
        for book, fighters in book_odds.items():
            if fight.fighter1 in fighters and fight.fighter2 in fighters:
                complete_books[book] = {
                    'fighter1': fighters[fight.fighter1],
                    'fighter2': fighters[fight.fighter2]
                }
        
        return complete_books
    
    def calculate_sharp_consensus(self, book_odds: Dict[str, Dict[str, int]]) -> Optional[Tuple[float, float]]:
        """Calculate consensus probability from sharp books"""
        sharp_f1_odds = []
        sharp_f2_odds = []
        
        for book, odds in book_odds.items():
            if book in self.sharp_books:
                sharp_f1_odds.append(odds['fighter1'])
                sharp_f2_odds.append(odds['fighter2'])
        
        if not sharp_f1_odds:
            print("⚠️ No sharp books found for consensus")
            return None
        
        # Average the sharp book odds
        avg_sharp_f1 = int(sum(sharp_f1_odds) / len(sharp_f1_odds))
        avg_sharp_f2 = int(sum(sharp_f2_odds) / len(sharp_f2_odds))
        
        # Get vig-free probabilities from sharp consensus
        sharp_prob1, sharp_prob2 = self.remove_vig(avg_sharp_f1, avg_sharp_f2)
        
        print(f"📊 Sharp consensus: F1: {avg_sharp_f1} ({sharp_prob1:.1%}) | F2: {avg_sharp_f2} ({sharp_prob2:.1%})")
        
        return sharp_prob1, sharp_prob2
    
    def calculate_fight_evs(self, fight: Fight, threshold: str = 'moderate') -> List[EVResult]:
        """Calculate EV opportunities for a single fight with Kelly sizing"""
        results = []
        
        print(f"\n🥊 Analyzing: {fight.fighter1} vs {fight.fighter2}")
        
        # Get organized odds data
        book_odds = self.get_book_odds_for_fight(fight)
        
        if len(book_odds) < 2:
            print("❌ Not enough books with complete odds")
            return []
        
        # Get sharp consensus
        sharp_consensus = self.calculate_sharp_consensus(book_odds)
        if not sharp_consensus:
            return []
        
        sharp_prob1, sharp_prob2 = sharp_consensus
        
        # Check each square book for EV opportunities
        for book, odds in book_odds.items():
            if book not in self.square_books:
                continue
            
            # Get vig-free probabilities from this square book
            square_prob1, square_prob2 = self.remove_vig(odds['fighter1'], odds['fighter2'])
            
            # Calculate EV for fighter 1
            ev_f1 = (sharp_prob1 - square_prob1) * 100
            
            # Calculate EV for fighter 2
            ev_f2 = (sharp_prob2 - square_prob2) * 100
            
            # Check if either fighter meets our threshold
            if ev_f1 >= self.ev_thresholds[threshold]:
                confidence = self.calculate_confidence_score(ev_f1, len([b for b in book_odds.keys() if b in self.sharp_books]))
                
                # Calculate Kelly sizing for fighter 1
                kelly_result = self.kelly_calc.calculate_kelly_size(
                    ev_percentage=ev_f1,
                    sharp_probability=sharp_prob1 * 100,
                    american_odds=odds['fighter1']
                )
                
                results.append(EVResult(
                    fighter=fight.fighter1,
                    book=book,
                    ev_percentage=round(ev_f1, 2),
                    confidence_score=round(confidence, 1),
                    sharp_consensus_prob=round(sharp_prob1 * 100, 1),
                    square_prob=round(square_prob1 * 100, 1),
                    recommendation=self.get_recommendation(ev_f1, confidence),
                    fight_info=f"{fight.fighter1} vs {fight.fighter2}",
                    kelly_size=kelly_result.recommended_percentage,
                    kelly_dollars=kelly_result.recommended_dollars,
                    kelly_units=kelly_result.unit_size,
                    kelly_category=kelly_result.kelly_category
                ))
                
                print(f"✅ +EV: {fight.fighter1} @ {book} (+{ev_f1:.1f}%) | Kelly: ${kelly_result.recommended_dollars} ({kelly_result.unit_size} units)")
            
            if ev_f2 >= self.ev_thresholds[threshold]:
                confidence = self.calculate_confidence_score(ev_f2, len([b for b in book_odds.keys() if b in self.sharp_books]))
                
                # Calculate Kelly sizing for fighter 2
                kelly_result = self.kelly_calc.calculate_kelly_size(
                    ev_percentage=ev_f2,
                    sharp_probability=sharp_prob2 * 100,
                    american_odds=odds['fighter2']
                )
                
                results.append(EVResult(
                    fighter=fight.fighter2,
                    book=book,
                    ev_percentage=round(ev_f2, 2),
                    confidence_score=round(confidence, 1),
                    sharp_consensus_prob=round(sharp_prob2 * 100, 1),
                    square_prob=round(square_prob2 * 100, 1),
                    recommendation=self.get_recommendation(ev_f2, confidence),
                    fight_info=f"{fight.fighter1} vs {fight.fighter2}",
                    kelly_size=kelly_result.recommended_percentage,
                    kelly_dollars=kelly_result.recommended_dollars,
                    kelly_units=kelly_result.unit_size,
                    kelly_category=kelly_result.kelly_category
                ))
                
                print(f"✅ +EV: {fight.fighter2} @ {book} (+{ev_f2:.1f}%) | Kelly: ${kelly_result.recommended_dollars} ({kelly_result.unit_size} units)")
        
        return sorted(results, key=lambda x: x.ev_percentage, reverse=True)
    
    def calculate_confidence_score(self, ev_percentage: float, sharp_books_count: int) -> float:
        """Calculate confidence score (0-100) for an EV opportunity"""
        score = 0
        
        # Base EV score (0-50 points)
        score += min(ev_percentage * 15, 50)
        
        # Multiple sharp books agreement (0-30 points)
        score += min(sharp_books_count * 10, 30)
        
        # Bonus for very high EV (0-20 points)
        if ev_percentage >= 3.0:
            score += 20
        elif ev_percentage >= 2.0:
            score += 15
        elif ev_percentage >= 1.5:
            score += 10
        
        return min(score, 100)
    
    def get_recommendation(self, ev_percentage: float, confidence_score: float) -> str:
        """Get betting recommendation based on EV and confidence"""
        if confidence_score >= 80 and ev_percentage >= 2.5:
            return "🔥 STRONG BET"
        elif confidence_score >= 60 and ev_percentage >= 1.5:
            return "✅ GOOD BET"
        elif ev_percentage >= 1.0:
            return "📊 DECENT BET"
        else:
            return "⚠️ SMALL EDGE"
    
    def analyze_all_fights(self, fights: List[Fight]) -> List[EVResult]:
        """Analyze all fights and return +EV opportunities with Kelly sizing"""
        all_evs = []
        
        for fight in fights:
            fight_evs = self.calculate_fight_evs(fight)
            all_evs.extend(fight_evs)
        
        # Sort by EV percentage (highest first)
        all_evs.sort(key=lambda x: x.ev_percentage, reverse=True)
        
        return all_evs
    
    def save_ev_results(self, ev_results: List[EVResult], filename: str = "../data/ev_opportunities.json"):
        """Save EV results to JSON file"""
        # Convert dataclasses to dictionaries
        results_dict = [asdict(result) for result in ev_results]
        
        with open(filename, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"💾 Saved {len(ev_results)} EV opportunities to {filename}")

def main():
    """Test the EV calculator with Kelly sizing"""
    print("🧮 Testing EV Calculator with Kelly Sizing...")
    
    # Load fights data (will be created by scraper)
    try:
        with open('../data/fights.json', 'r') as f:
            fights_data = json.load(f)
        
        # Convert back to Fight objects
        fights = []
        for fight_dict in fights_data:
            odds_data = [FighterOdds(**odds) for odds in fight_dict['odds_data']]
            fight = Fight(
                fighter1=fight_dict['fighter1'],
                fighter2=fight_dict['fighter2'],
                event_name=fight_dict['event_name'],
                event_date=fight_dict['event_date'],
                weight_class=fight_dict['weight_class'],
                odds_data=odds_data,
                scraped_at=fight_dict['scraped_at']
            )
            fights.append(fight)
            
    except FileNotFoundError:
        print("No fights.json found - run scraper.py first!")
        return
    
    # Calculate EVs with Kelly sizing
    calculator = EVCalculator()
    ev_results = calculator.analyze_all_fights(fights)
    
    # Display results
    if ev_results:
        print(f"\n🎯 Found {len(ev_results)} +EV opportunities:")
        print("-" * 80)
        
        for ev in ev_results:
            print(f"{ev.recommendation}")
            print(f"   {ev.fighter} @ {ev.book}")
            print(f"   EV: +{ev.ev_percentage}% | Confidence: {ev.confidence_score}/100")
            print(f"   Sharp: {ev.sharp_consensus_prob}% | {ev.book}: {ev.square_prob}%")
            print(f"   💰 Kelly: {ev.kelly_category} | ${ev.kelly_dollars} ({ev.kelly_units} units)")
            print()
        
        # Save results
        calculator.save_ev_results(ev_results)
    else:
        print("❌ No +EV opportunities found")

if __name__ == "__main__":
    main()