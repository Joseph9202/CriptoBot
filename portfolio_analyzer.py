#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings

warnings.filterwarnings('ignore')

class PortfolioAnalyzer:
    """
    Analizador avanzado de portfolio para el bot de trading
    """
    
    def __init__(self, db_path: str = 'trading_bot.db'):
        self.db_path = db_path
        self.trades_df = None
        self.portfolio_history_df = None
        self.load_data()
    
    def load_data(self):
        """Carga datos desde la base de datos"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Cargar trades
            self.trades_df = pd.read_sql_query("""
                SELECT * FROM trades 
                WHERE status = 'CLOSED'
                ORDER BY entry_time
            """, conn)
            
            if not self.trades_df.empty:
                self.trades_df['entry_time'] = pd.to_datetime(self.trades_df['entry_time'])
                self.trades_df['exit_time'] = pd.to_datetime(self.trades_df['exit_time'])
                self.trades_df['duration'] = self.trades_df['exit_time'] - self.trades_df['entry_time']
                self.trades_df['duration_hours'] = self.trades_df['duration'].dt.total_seconds() / 3600
            
            # Cargar historial de portfolio
            self.portfolio_history_df = pd.read_sql_query("""
                SELECT * FROM portfolio_history 
                ORDER BY timestamp
            """, conn)
            
            if not self.portfolio_history_df.empty:
                self.portfolio_history_df['timestamp'] = pd.to_datetime(self.portfolio_history_df['timestamp'])
            
            conn.close()
            
        except Exception as e:
            print(f"Error cargando datos: {e}")
            self.trades_df = pd.DataFrame()
            self.portfolio_history_df = pd.DataFrame()
    
    def calculate_performance_metrics(self) -> Dict:
        """Calcula métricas de rendimiento del portfolio"""
        if self.trades_df.empty:
            return {}
        
        # Métricas básicas
        total_trades = len(self.trades_df)
        winning_trades = len(self.trades_df[self.trades_df['pnl'] > 0])
        losing_trades = len(self.trades_df[self.trades_df['pnl'] < 0])
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # P&L metrics
        total_pnl = self.trades_df['pnl'].sum()
        avg_win = self.trades_df[self.trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = self.trades_df[self.trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        # Risk metrics
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else float('inf')
        
        # Drawdown calculation
        cumulative_pnl = self.trades_df['pnl'].cumsum()
        running_max = cumulative_pnl.expanding().max()
        drawdown = (cumulative_pnl - running_max) / running_max.abs()
        max_drawdown = drawdown.min() * 100
        
        # Sharpe ratio (simplified)
        returns = self.trades_df['pnl_pct']
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        # Trade duration analysis
        avg_duration = self.trades_df['duration_hours'].mean()
        
        # Best and worst trades
        best_trade = self.trades_df.loc[self.trades_df['pnl'].idxmax()] if not self.trades_df.empty else None
        worst_trade = self.trades_df.loc[self.trades_df['pnl'].idxmin()] if not self.trades_df.empty else None
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'avg_duration_hours': avg_duration,
            'best_trade': best_trade,
            'worst_trade': worst_trade
        }
    
    def generate_performance_report(self) -> str:
        """Genera reporte textual de rendimiento"""
        metrics = self.calculate_performance_metrics()
        
        if not metrics:
            return "No hay datos suficientes para generar el reporte."
        
        report = []
        report.append("=" * 80)
        report.append("📊 REPORTE DE PERFORMANCE DETALLADO")
        report.append("=" * 80)
        
        # Métricas generales
        report.append(f"\n📈 MÉTRICAS GENERALES:")
        report.append(f"   Total de Trades: {metrics['total_trades']:,}")
        report.append(f"   Trades Ganadores: {metrics['winning_trades']:,}")
        report.append(f"   Trades Perdedores: {metrics['losing_trades']:,}")
        report.append(f"   Win Rate: {metrics['win_rate']:.2f}%")
        
        # Métricas de P&L
        report.append(f"\n💰 MÉTRICAS DE P&L:")
        report.append(f"   P&L Total: ${metrics['total_pnl']:,.2f}")
        report.append(f"   Ganancia Promedio: ${metrics['avg_win']:,.2f}")
        report.append(f"   Pérdida Promedio: ${metrics['avg_loss']:,.2f}")
        report.append(f"   Factor de Ganancia: {metrics['profit_factor']:.2f}")
        
        # Métricas de riesgo
        report.append(f"\n⚠️ MÉTRICAS DE RIESGO:")
        report.append(f"   Max Drawdown: {metrics['max_drawdown']:.2f}%")
        report.append(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
        
        # Análisis temporal
        report.append(f"\n⏰ ANÁLISIS TEMPORAL:")
        report.append(f"   Duración Promedio: {metrics['avg_duration_hours']:.1f} horas")
        
        # Mejores y peores trades
        if metrics['best_trade'] is not None:
            best = metrics['best_trade']
            report.append(f"\n🏆 MEJOR TRADE:")
            report.append(f"   {best['symbol']} - {best['side']} @ ${best['entry_price']:.2f}")
            report.append(f"   P&L: ${best['pnl']:.2f} ({best['pnl_pct']:.2f}%)")
            report.append(f"   Fecha: {best['entry_time']}")
        
        if metrics['worst_trade'] is not None:
            worst = metrics['worst_trade']
            report.append(f"\n📉 PEOR TRADE:")
            report.append(f"   {worst['symbol']} - {worst['side']} @ ${worst['entry_price']:.2f}")
            report.append(f"   P&L: ${worst['pnl']:.2f} ({worst['pnl_pct']:.2f}%)")
            report.append(f"   Fecha: {worst['entry_time']}")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def plot_equity_curve(self, save_path: str = None):
        """Genera gráfico de curva de capital"""
        if self.trades_df.empty:
            print("No hay datos para graficar")
            return
        
        # Calcular curva de capital
        initial_balance = 10000  # Valor por defecto
        cumulative_pnl = self.trades_df['pnl'].cumsum()
        equity_curve = initial_balance + cumulative_pnl
        
        # Crear gráfico
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
        
        # Curva de capital
        ax1.plot(self.trades_df['exit_time'], equity_curve, linewidth=2, color='blue', label='Balance')
        ax1.axhline(y=initial_balance, color='red', linestyle='--', alpha=0.7, label='Balance Inicial')
        ax1.set_title('Curva de Capital del Portfolio', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Balance ($)', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # P&L por trade
        colors = ['green' if pnl > 0 else 'red' for pnl in self.trades_df['pnl']]
        ax2.bar(range(len(self.trades_df)), self.trades_df['pnl'], color=colors, alpha=0.7)
        ax2.set_title('P&L por Trade', fontsize=16, fontweight='bold')
        ax2.set_xlabel('Número de Trade', fontsize=12)
        ax2.set_ylabel('P&L ($)', fontsize=12)
        ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def plot_trade_analysis(self, save_path: str = None):
        """Genera análisis visual de trades"""
        if self.trades_df.empty:
            print("No hay datos para graficar")
            return
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # 1. Distribución de P&L
        ax1.hist(self.trades_df['pnl'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.axvline(x=0, color='red', linestyle='--', alpha=0.7)
        ax1.set_title('Distribución de P&L por Trade', fontweight='bold')
        ax1.set_xlabel('P&L ($)')
        ax1.set_ylabel('Frecuencia')
        ax1.grid(True, alpha=0.3)
        
        # 2. Win Rate por símbolo
        symbol_stats = self.trades_df.groupby('symbol').agg({
            'pnl': ['count', lambda x: (x > 0).sum()]
        }).round(2)
        symbol_stats.columns = ['total_trades', 'winning_trades']
        symbol_stats['win_rate'] = (symbol_stats['winning_trades'] / symbol_stats['total_trades'] * 100).round(1)
        
        if len(symbol_stats) > 0:
            ax2.bar(symbol_stats.index, symbol_stats['win_rate'], color='green', alpha=0.7)
            ax2.set_title('Win Rate por Símbolo', fontweight='bold')
            ax2.set_ylabel('Win Rate (%)')
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
        
        # 3. Duración vs P&L
        if 'duration_hours' in self.trades_df.columns:
            scatter_colors = ['green' if pnl > 0 else 'red' for pnl in self.trades_df['pnl']]
            ax3.scatter(self.trades_df['duration_hours'], self.trades_df['pnl'], 
                       c=scatter_colors, alpha=0.6, s=50)
            ax3.set_title('Duración vs P&L', fontweight='bold')
            ax3.set_xlabel('Duración (horas)')
            ax3.set_ylabel('P&L ($)')
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            ax3.grid(True, alpha=0.3)
        
        # 4. Evolución del win rate
        win_rate_evolution = []
        for i in range(1, len(self.trades_df) + 1):
            trades_subset = self.trades_df.iloc[:i]
            wins = len(trades_subset[trades_subset['pnl'] > 0])
            win_rate = (wins / i) * 100
            win_rate_evolution.append(win_rate)
        
        ax4.plot(range(1, len(self.trades_df) + 1), win_rate_evolution, linewidth=2, color='purple')
        ax4.set_title('Evolución del Win Rate', fontweight='bold')
        ax4.set_xlabel('Número de Trade')
        ax4.set_ylabel('Win Rate (%)')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        
        plt.show()
    
    def create_interactive_dashboard(self, save_path: str = "portfolio_dashboard.html"):
        """Crea dashboard interactivo con Plotly"""
        if self.trades_df.empty:
            print("No hay datos para crear dashboard")
            return
        
        # Preparar datos
        initial_balance = 10000
        cumulative_pnl = self.trades_df['pnl'].cumsum()
        equity_curve = initial_balance + cumulative_pnl
        
        # Crear subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=('Curva de Capital', 'P&L por Trade', 
                          'Distribución de P&L', 'Win Rate por Símbolo',
                          'Duración vs P&L', 'Evolución del Win Rate'),
            vertical_spacing=0.08,
            horizontal_spacing=0.1
        )
        
        # 1. Curva de capital
        fig.add_trace(
            go.Scatter(x=self.trades_df['exit_time'], y=equity_curve,
                      mode='lines', name='Balance', line=dict(color='blue', width=2)),
            row=1, col=1
        )
        
        # 2. P&L por trade
        colors = ['green' if pnl > 0 else 'red' for pnl in self.trades_df['pnl']]
        fig.add_trace(
            go.Bar(x=list(range(len(self.trades_df))), y=self.trades_df['pnl'],
                   marker_color=colors, name='P&L por Trade', showlegend=False),
            row=1, col=2
        )
        
        # 3. Distribución de P&L
        fig.add_trace(
            go.Histogram(x=self.trades_df['pnl'], nbinsx=20, name='Distribución P&L',
                        marker_color='skyblue', showlegend=False),
            row=2, col=1
        )
        
        # 4. Win Rate por símbolo
        symbol_stats = self.trades_df.groupby('symbol').agg({
            'pnl': ['count', lambda x: (x > 0).sum()]
        })
        symbol_stats.columns = ['total_trades', 'winning_trades']
        symbol_stats['win_rate'] = (symbol_stats['winning_trades'] / symbol_stats['total_trades'] * 100)
        
        fig.add_trace(
            go.Bar(x=symbol_stats.index, y=symbol_stats['win_rate'],
                   marker_color='green', name='Win Rate', showlegend=False),
            row=2, col=2
        )
        
        # 5. Duración vs P&L
        if 'duration_hours' in self.trades_df.columns:
            colors_scatter = ['green' if pnl > 0 else 'red' for pnl in self.trades_df['pnl']]
            fig.add_trace(
                go.Scatter(x=self.trades_df['duration_hours'], y=self.trades_df['pnl'],
                          mode='markers', marker=dict(color=colors_scatter),
                          name='Duración vs P&L', showlegend=False),
                row=3, col=1
            )
        
        # 6. Evolución del win rate
        win_rate_evolution = []
        for i in range(1, len(self.trades_df) + 1):
            trades_subset = self.trades_df.iloc[:i]
            wins = len(trades_subset[trades_subset['pnl'] > 0])
            win_rate = (wins / i) * 100
            win_rate_evolution.append(win_rate)
        
        fig.add_trace(
            go.Scatter(x=list(range(1, len(self.trades_df) + 1)), y=win_rate_evolution,
                      mode='lines', line=dict(color='purple', width=2),
                      name='Win Rate Evolution', showlegend=False),
            row=3, col=2
        )
        
        # Actualizar layout
        fig.update_layout(
            height=900,
            showlegend=True,
            title_text="📊 Dashboard de Trading - Análisis de Performance",
            title_font_size=20
        )
        
        # Guardar
        fig.write_html(save_path)
        print(f"Dashboard guardado en: {save_path}")
        
        return fig
    
    def export_trades_to_excel(self, file_path: str = "trades_analysis.xlsx"):
        """Exporta análisis de trades a Excel"""
        if self.trades_df.empty:
            print("No hay datos para exportar")
            return
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            # Hoja 1: Todos los trades
            self.trades_df.to_excel(writer, sheet_name='All_Trades', index=False)
            
            # Hoja 2: Resumen por símbolo
            symbol_summary = self.trades_df.groupby('symbol').agg({
                'pnl': ['count', 'sum', 'mean', lambda x: (x > 0).sum()],
                'pnl_pct': ['mean', 'std'],
                'duration_hours': 'mean'
            }).round(4)
            symbol_summary.columns = ['Total_Trades', 'Total_PnL', 'Avg_PnL', 'Winning_Trades',
                                    'Avg_PnL_Pct', 'PnL_Volatility', 'Avg_Duration_Hours']
            symbol_summary['Win_Rate'] = (symbol_summary['Winning_Trades'] / symbol_summary['Total_Trades'] * 100).round(2)
            symbol_summary.to_excel(writer, sheet_name='Symbol_Summary')
            
            # Hoja 3: Métricas de performance
            metrics = self.calculate_performance_metrics()
            metrics_df = pd.DataFrame(list(metrics.items()), columns=['Metric', 'Value'])
            metrics_df = metrics_df[~metrics_df['Metric'].isin(['best_trade', 'worst_trade'])]  # Excluir objetos
            metrics_df.to_excel(writer, sheet_name='Performance_Metrics', index=False)
        
        print(f"Análisis exportado a: {file_path}")

def main():
    """Función principal para análisis de portfolio"""
    print("📊 PORTFOLIO ANALYZER - Análisis Avanzado de Trading")
    
    analyzer = PortfolioAnalyzer()
    
    if analyzer.trades_df.empty:
        print("❌ No se encontraron trades en la base de datos.")
        print("Ejecuta primero el bot de trading para generar datos.")
        return
    
    print(f"✅ Cargados {len(analyzer.trades_df)} trades para análisis")
    
    # Generar reporte de performance
    print("\n📈 Generando reporte de performance...")
    report = analyzer.generate_performance_report()
    print(report)
    
    # Preguntar qué análisis realizar
    print("\n🔍 OPCIONES DE ANÁLISIS:")
    print("1. Gráficos estáticos (matplotlib)")
    print("2. Dashboard interactivo (HTML)")
    print("3. Exportar a Excel")
    print("4. Todo lo anterior")
    
    choice = input("\nElige opción (1-4): ").strip()
    
    if choice in ['1', '4']:
        print("\n📊 Generando gráficos de curva de capital...")
        analyzer.plot_equity_curve()
        
        print("📊 Generando análisis de trades...")
        analyzer.plot_trade_analysis()
    
    if choice in ['2', '4']:
        print("\n🌐 Creando dashboard interactivo...")
        analyzer.create_interactive_dashboard()
    
    if choice in ['3', '4']:
        print("\n📋 Exportando análisis a Excel...")
        analyzer.export_trades_to_excel()
    
    print("\n✅ Análisis completado!")

if __name__ == "__main__":
    main()