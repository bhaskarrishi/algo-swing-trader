"""Backtesting engine for strategy validation."""
import pandas as pd
from typing import Dict, List
from datetime import datetime
from app.core.indicators import indicators
from app.core.signals import signal_generator
from app.utils.logger import logger


class Backtester:
    """Backtesting engine."""
    
    def __init__(self, initial_capital: float = 100000):
        """Initialize backtester.
        
        Args:
            initial_capital: Starting capital
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = []
        self.closed_trades = []
        self.equity_curve = []
    
    def run(self, data: pd.DataFrame, symbol: str) -> Dict:
        """Run backtest on historical data.
        
        Args:
            data: DataFrame with OHLCV data
            symbol: Stock symbol
            
        Returns:
            Backtest results
        """
        logger.info(f"Running backtest for {symbol} with {len(data)} bars")
        
        # Calculate indicators
        df = indicators.calculate_all_indicators(data)
        
        # Iterate through data
        for i in range(200, len(df)):  # Start after enough data for indicators
            current_bar = df.iloc[i]
            
            # Check for entry signals if no position
            if not self.positions:
                signal = signal_generator.generate_signal(df.iloc[:i+1], symbol)
                
                if signal:
                    self._enter_trade(signal, current_bar)
            
            # Check for exit conditions if in position
            else:
                for position in self.positions[:]:  # Copy list to allow removal
                    self._check_exit(position, current_bar)
            
            # Record equity
            self._record_equity(current_bar)
        
        # Close any remaining positions
        if self.positions:
            for position in self.positions:
                self._close_trade(position, df.iloc[-1]['close'], "End of backtest")
        
        return self._generate_report()
    
    def _enter_trade(self, signal: Dict, bar: pd.Series):
        """Enter a new trade.
        
        Args:
            signal: Trading signal
            bar: Current bar data
        """
        # Calculate position size (simplified - use 10% of capital)
        position_value = self.capital * 0.1
        quantity = int(position_value / signal['price'])
        
        if quantity == 0:
            return
        
        position = {
            'symbol': signal['symbol'],
            'side': signal['side'],
            'quantity': quantity,
            'entry_price': signal['price'],
            'entry_time': bar.name,
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit']
        }
        
        self.positions.append(position)
        self.capital -= quantity * signal['price']
        
        logger.debug(f"Entered {signal['side']} position: {quantity} @ ${signal['price']:.2f}")
    
    def _check_exit(self, position: Dict, bar: pd.Series):
        """Check if position should be exited.
        
        Args:
            position: Position dict
            bar: Current bar data
        """
        current_price = bar['close']
        
        # Check stop loss
        if position['side'] == 'BUY' and current_price <= position['stop_loss']:
            self._close_trade(position, current_price, "Stop loss")
            return
        elif position['side'] == 'SELL' and current_price >= position['stop_loss']:
            self._close_trade(position, current_price, "Stop loss")
            return
        
        # Check take profit
        if position['side'] == 'BUY' and current_price >= position['take_profit']:
            self._close_trade(position, current_price, "Take profit")
            return
        elif position['side'] == 'SELL' and current_price <= position['take_profit']:
            self._close_trade(position, current_price, "Take profit")
            return
    
    def _close_trade(self, position: Dict, exit_price: float, exit_reason: str):
        """Close a trade.
        
        Args:
            position: Position dict
            exit_price: Exit price
            exit_reason: Reason for exit
        """
        if position['side'] == 'BUY':
            pnl = (exit_price - position['entry_price']) * position['quantity']
        else:
            pnl = (position['entry_price'] - exit_price) * position['quantity']
        
        pnl_pct = (pnl / (position['entry_price'] * position['quantity'])) * 100
        
        self.capital += position['quantity'] * exit_price
        
        trade = {
            **position,
            'exit_price': exit_price,
            'exit_reason': exit_reason,
            'pnl': pnl,
            'pnl_pct': pnl_pct
        }
        
        self.closed_trades.append(trade)
        self.positions.remove(position)
        
        logger.debug(f"Closed position: P&L ${pnl:.2f} ({pnl_pct:.2f}%) - {exit_reason}")
    
    def _record_equity(self, bar: pd.Series):
        """Record current equity.
        
        Args:
            bar: Current bar data
        """
        position_value = sum(
            p['quantity'] * bar['close'] for p in self.positions
        )
        total_equity = self.capital + position_value
        
        self.equity_curve.append({
            'timestamp': bar.name,
            'equity': total_equity
        })
    
    def _generate_report(self) -> Dict:
        """Generate backtest report.
        
        Returns:
            Report dictionary
        """
        if not self.closed_trades:
            return {'total_trades': 0, 'error': 'No trades executed'}
        
        total_trades = len(self.closed_trades)
        winning_trades = [t for t in self.closed_trades if t['pnl'] > 0]
        losing_trades = [t for t in self.closed_trades if t['pnl'] <= 0]
        
        total_pnl = sum(t['pnl'] for t in self.closed_trades)
        win_rate = (len(winning_trades) / total_trades) * 100
        
        final_equity = self.equity_curve[-1]['equity'] if self.equity_curve else self.initial_capital
        total_return = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_pnl': total_pnl,
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            'avg_loss': sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0,
            'largest_win': max((t['pnl'] for t in winning_trades), default=0),
            'largest_loss': min((t['pnl'] for t in losing_trades), default=0),
            'equity_curve': self.equity_curve,
            'trades': self.closed_trades
        }
