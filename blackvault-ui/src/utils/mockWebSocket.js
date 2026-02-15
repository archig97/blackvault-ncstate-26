/**
 * Mock WebSocket Service - PaySim Dataset Style
 * Simulates real-time transaction data matching backend contract
 * Can be easily replaced with actual WebSocket connection later
 */

class MockWebSocket {
  constructor() {
    this.listeners = [];
    this.isConnected = false;
    this.interval = null;
    this.currentStep = 1; // Simulate time progression (1 step = 1 hour)
  }

  // Connect to mock WebSocket
  connect(onMessage, onError = null) {
    this.isConnected = true;
    console.log('🔌 Mock WebSocket connected (PaySim-style data)');

    // Simulate receiving messages every 1-2 seconds
    this.interval = setInterval(() => {
      const transaction = this.generateTransaction();
      if (onMessage) {
        onMessage(transaction);
      }
      this.currentStep++; // Advance simulation time
    }, 1000 + Math.random() * 1000); // Random interval between 1-2 seconds

    return () => this.disconnect();
  }

  // Disconnect from mock WebSocket
  disconnect() {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    this.isConnected = false;
    console.log('🔌 Mock WebSocket disconnected');
  }

  // Generate realistic transaction data (matches backend contract)
  generateTransaction() {
    const transactionTypes = ['CASH_IN', 'CASH_OUT', 'DEBIT', 'PAYMENT', 'TRANSFER'];
    const type = transactionTypes[Math.floor(Math.random() * transactionTypes.length)];

    // Fraud is more common in TRANSFER and CASH_OUT (realistic!)
    const isFraudulent = (type === 'TRANSFER' || type === 'CASH_OUT') && Math.random() < 0.02;

    const amount = isFraudulent
      ? Math.random() * 500000 + 100000  // Large amounts for fraud
      : Math.random() * 10000;            // Normal amounts

    const oldBalanceOrg = Math.random() * 1000000;
    const newBalanceOrig = Math.max(0, oldBalanceOrg - amount);

    const oldBalanceDest = Math.random() * 500000;
    const newBalanceDest = type === 'PAYMENT' ? oldBalanceDest : oldBalanceDest + amount;

    // Calculate risk score
    const riskScore = this.calculateRiskScore({
      type,
      amount,
      oldBalanceOrg,
      newBalanceOrig,
      oldBalanceDest,
      newBalanceDest,
      isFraudulent
    });

    return {
      // ===== FROM PERSON 1 (Valkey Storage) =====
      transaction: {
        id: `tx_${Math.random().toString(36).substring(2, 9)}`,
        step: this.currentStep,
        timestamp: new Date().toISOString(),
        type: type,
        amount: parseFloat(amount.toFixed(2)),
        sender: `C${Math.floor(Math.random() * 9000000000 + 1000000000)}`,
        receiver: type === 'PAYMENT'
          ? `M${Math.floor(Math.random() * 9000000000 + 1000000000)}` // Merchant
          : `C${Math.floor(Math.random() * 9000000000 + 1000000000)}`, // Customer
        oldBalanceOrg: parseFloat(oldBalanceOrg.toFixed(2)),
        newBalanceOrig: parseFloat(newBalanceOrig.toFixed(2)),
        oldBalanceDest: parseFloat(oldBalanceDest.toFixed(2)),
        newBalanceDest: parseFloat(newBalanceDest.toFixed(2)),
        isFraud: isFraudulent ? 1 : 0,
      },

      // ===== FROM PERSON 2 (Risk Engine) =====
      risk_score: {
        risk: riskScore,
        flagged: riskScore > 70,
        reasons: this.generateReasons(riskScore, type, amount, newBalanceOrig),
        breakdown: {
          amount_component: this.getAmountRisk(amount),
          balance_component: this.getBalanceRisk(newBalanceOrig, oldBalanceOrg),
          type_component: this.getTypeRisk(type),
          pattern_component: Math.random() * 30,
        }
      },

      // ===== FROM PERSON 4 (Graph Metrics) =====
      graph_metrics: {
        hops_to_bad: isFraudulent ? Math.floor(Math.random() * 2) : Math.floor(Math.random() * 5),
        neighbor_count: Math.floor(Math.random() * 20),
        risk_density: parseFloat((isFraudulent ? Math.random() * 0.5 + 0.5 : Math.random() * 0.3).toFixed(2)),
        structural_risk: parseFloat((isFraudulent ? Math.random() * 0.4 + 0.6 : Math.random() * 0.5).toFixed(2)),
        edge_churn: parseFloat((Math.random() * 0.5).toFixed(2)),
      },

      // ===== FROM PERSON 1 (Feature Store - Advanced Metrics) =====
      advanced_metrics: {
        velocity_1h: Math.floor(Math.random() * 50),
        velocity_24h: Math.floor(Math.random() * 500),
        velocity_7d: Math.floor(Math.random() * 2000),
        velocity_30d: Math.floor(Math.random() * 5000),

        velocity_z: parseFloat((isFraudulent ? Math.random() * 3 + 1 : Math.random() * 2 - 0.5).toFixed(2)),
        dispersion_z: parseFloat((Math.random() * 4 - 1).toFixed(2)),

        entropy_shift: parseFloat((isFraudulent ? Math.random() * 0.5 + 0.5 : Math.random() * 0.3).toFixed(2)),
        drain_ratio: parseFloat((newBalanceOrig === 0 ? 1.0 : (oldBalanceOrg - newBalanceOrig) / oldBalanceOrg).toFixed(2)),
        drift_indicator: parseFloat((Math.random() * 2 - 1).toFixed(2)),
        micro_pattern_score: parseFloat((Math.random()).toFixed(2)),

        suspicion_memory: parseFloat((isFraudulent ? Math.random() * 30 + 20 : Math.random() * 15).toFixed(1)),
        previous_risk: parseFloat((Math.random() * 100).toFixed(1)),
        behavioral_drift_score: parseFloat((Math.random() * 3).toFixed(2)),

        account_age_days: Math.floor(Math.random() * 365),
        maturity_penalty: parseFloat((Math.random() * 0.5).toFixed(2)),
      },

      // ===== UI-SPECIFIC FLAGS =====
      ui_flags: {
        is_new_account: Math.random() > 0.9,
        structural_instability: isFraudulent && Math.random() > 0.5,
        suspicion_trending_up: isFraudulent || Math.random() > 0.7,
        activity_level: this.getActivityLevel(),
        is_zero_balance: newBalanceOrig === 0,
        is_merchant_payment: type === 'PAYMENT',
      }
    };
  }

  calculateRiskScore({ type, amount, oldBalanceOrg, newBalanceOrig, oldBalanceDest, newBalanceDest, isFraudulent }) {
    let risk = 0;

    // High amount risk
    if (amount > 200000) risk += 40;
    else if (amount > 100000) risk += 30;
    else if (amount > 50000) risk += 20;
    else if (amount > 10000) risk += 10;

    // Zero balance after transaction (drain)
    if (newBalanceOrig === 0 && oldBalanceOrg > 0) risk += 25;

    // Suspicious destination balance
    if (newBalanceDest === 0 && type !== 'PAYMENT') risk += 20;

    // Transaction type risk
    if (type === 'TRANSFER' || type === 'CASH_OUT') risk += 15;

    // If actually fraudulent, boost score
    if (isFraudulent) risk = Math.min(100, risk + 30);

    return Math.min(100, Math.floor(risk + Math.random() * 10));
  }

  getAmountRisk(amount) {
    if (amount > 200000) return 40;
    if (amount > 100000) return 30;
    if (amount > 50000) return 20;
    if (amount > 10000) return 10;
    return 5;
  }

  getBalanceRisk(newBalance, oldBalance) {
    if (newBalance === 0 && oldBalance > 0) return 30;
    if (newBalance < oldBalance * 0.1) return 20;
    return 5;
  }

  getTypeRisk(type) {
    if (type === 'TRANSFER') return 20;
    if (type === 'CASH_OUT') return 15;
    if (type === 'DEBIT') return 10;
    return 5;
  }

  generateReasons(riskValue, type, amount, newBalance) {
    const reasons = [];

    if (riskValue > 80) {
      reasons.push("🚨 Critical: High-value transaction detected");
      if (newBalance === 0) reasons.push("⚠️ Account drained to zero");
      if (type === 'TRANSFER') reasons.push("⚠️ Suspicious transfer pattern");
    } else if (riskValue > 60) {
      reasons.push("⚠️ Warning: Unusual transaction amount");
      if (amount > 100000) reasons.push(`💰 Large amount: $${amount.toFixed(2)}`);
    } else if (riskValue > 40) {
      reasons.push("ℹ️ Moderate: Elevated activity detected");
    }

    return reasons;
  }

  getActivityLevel() {
    const rand = Math.random();
    if (rand > 0.7) return 'high';
    if (rand > 0.3) return 'medium';
    return 'low';
  }

  // Simulate batch data for initial load
  generateBatch(count = 10) {
    return Array.from({ length: count }, () => this.generateTransaction());
  }
}

// Export singleton instance
export const mockWebSocket = new MockWebSocket();

// Helper to format timestamp for display
export function formatTimestamp(isoString) {
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}
