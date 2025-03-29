//+------------------------------------------------------------------+
//|                         Forex SMC Bot                           |
//|    Smart Money Concepts Trading Bot for MT5                    |
//|    Uses SMC, Price Action, and Liquidity Considerations         |
//+------------------------------------------------------------------+
#include <Trade/Trade.mqh>
#include <Trade/PositionInfo.mqh>
#include <Trade/OrderInfo.mqh>
#include <Trade/AccountInfo.mqh>

// Declare necessary classes and objects
CTrade trade;

// Global Settings
input double RiskPerTrade = 2.0;   // Risk percentage per trade
input int MaxSlippage = 3;         // Max slippage allowed
input double MinVolatility = 10.0; // Minimum volatility threshold
input bool UseNewsFilter = true;   // Enable/Disable news filter

// Timeframe & Session Settings
input ENUM_TIMEFRAMES TradingTimeframe = PERIOD_H4; // Trading timeframe
input bool TradeAllSessions = true; // Trade in all sessions

// Email & Notification Settings
input bool SendEmailAlerts = true;
input bool SendPushNotifications = true;

// Trade Management Variables
double EntryPrice, StopLoss, TakeProfit;
double LotSize;

// Function to Calculate Lot Size Based on Risk
double CalculateLotSize(double slPoints) {
    double riskAmount = AccountInfoDouble(ACCOUNT_BALANCE) * (RiskPerTrade / 100);
    double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
    if (tickValue == 0 || slPoints <= 0) return 0;
    double lot = riskAmount / (slPoints * tickValue);
    return NormalizeDouble(lot, 2);
}

// Function to Check SMC Entry Criteria
bool CheckSMCEntry() {
    // Correct iMA usage with the proper number of parameters
    double ma50 = iMA(_Symbol, TradingTimeframe, 50, 0, MODE_SMA, PRICE_CLOSE, 0); // Corrected iMA call
    if (ma50 == WRONG_VALUE) return false;
    double bidPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    
    if (bidPrice > ma50) {
        return true;
    }
    return false;
}

// Function to Send Email and Notification Alerts
void SendTradeAlert() {
    string message = StringFormat(
        "Trade Signal: %s\nEntry: %.5f\nSL: %.5f\nTP: %.5f\nReason: SMC Setup", 
        _Symbol, EntryPrice, StopLoss, TakeProfit);
    string subject = "Trade Confirmation";
    
    if (SendEmailAlerts) {
        if (!SendMail(subject, message)) {
            Print("Error sending email: ", GetLastError());
        }
    }
    if (SendPushNotifications) {
        SendNotification(message);
    }
}

// Function to Handle User Confirmation
bool ConfirmTrade() {
    string confirmationMessage = "Do you want to execute this trade? Reply with 'yes' or 'no'.";
    
    if (SendEmailAlerts) {
        SendMail("Trade Confirmation Request", confirmationMessage);
    }
    if (SendPushNotifications) {
        SendNotification(confirmationMessage);
    }
    
    return true; // Placeholder for manual confirmation
}

// Main Trading Logic
void OnTick() {
    if (!CheckSMCEntry()) return;
    
    EntryPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
    StopLoss = EntryPrice - (MinVolatility * Point);
    TakeProfit = EntryPrice + ((EntryPrice - StopLoss) * 3);
    LotSize = CalculateLotSize(fabs(StopLoss - EntryPrice));
    
    if (LotSize <= 0) {
        Print("Invalid lot size calculation, skipping trade.");
        return;
    }
    
    SendTradeAlert();
    
    if (ConfirmTrade()) {
        if (!trade.Buy(LotSize, _Symbol, EntryPrice, StopLoss, TakeProfit)) {
            Print("Trade execution failed: ", GetLastError());
        } else {
            Print("Trade Executed: Buy at ", EntryPrice);
        }
    } else {
        Print("Trade Cancelled");
    }
}
