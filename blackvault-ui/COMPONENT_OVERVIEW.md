# BlackVault UI - Component Overview

## 📊 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  🔐 BlackVault Dashboard                                        │
│  Real-time transaction monitoring and risk analysis             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────┐│
│  │ Total Trans  │ │  Avg Risk    │ │ Total Volume │ │ Flagged ││
│  │     15       │ │    67.3      │ │  $45,234.56  │ │    3    ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └─────────┘│
│                                                                 │
│  ┌────────────────────────┐ ┌────────────────────────┐         │
│  │ Risk Distribution      │ │ Structural Instability │         │
│  │ Low: 5  Med: 7  Hi: 3  │ │ 2 (13.3%)              │         │
│  └────────────────────────┘ └────────────────────────┘         │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  🔴 Live Transaction Feed                        ● Live        │
├─────────────────────────────────────────────────────────────────┤
│  Time     │ Sender    │ Receiver  │ Amount  │ Risk │ Drift │...│
│───────────┼───────────┼───────────┼─────────┼──────┼───────┼───│
│  14:23:45 │ acct_0123 │ acct_0456 │ $1,234  │  85  │ +0.67 │⚠️ │
│  14:23:43 │ acct_0789 │ acct_0012 │ $5,678  │  42  │ -0.23 │↘️ │
│  14:23:41 │ acct_0345 │ acct_0678 │ $9,012  │  91  │ +0.89 │⚠️↗│
│  ...                                                            │
├─────────────────────────────────────────────────────────────────┤
│  Legend: Risk: [0-50] [51-80] [81-100]                         │
│          Drift: Behavioral deviation indicator                 │
│          Flags: ⚠️ Structural instability, ↗️↘️ Suspicion trend │
└─────────────────────────────────────────────────────────────────┘
```

## 🎨 Color Coding

### Risk Levels
- **🟢 Low (0-50)**: Green badges and text
- **🟡 Medium (51-80)**: Yellow badges and text
- **🔴 High (81-100)**: Red badges and text

### Activity Levels
- **🟢 LOW**: Green badge with border
- **🟡 MEDIUM**: Yellow badge with border
- **🔴 HIGH**: Red badge with border

### Drift Indicator
- **🔵 Negative (<-0.5)**: Blue text (below normal)
- **⚪ Neutral (-0.5 to 0.5)**: Gray text (normal)
- **🔴 Positive (>0.5)**: Red text (above normal)

### Special Flags
- **⚠️ Orange**: Structural instability detected
- **↗️ Red**: Suspicion trending up
- **↘️ Green**: Suspicion trending down

## 📱 Component Breakdown

### 1. StatsPanel Component
**Purpose**: Real-time statistics overview
**Updates**: Every time a new transaction arrives
**Metrics**:
- Total transaction count
- Average risk score (color-coded)
- Total transaction volume
- Number of flagged transactions
- Risk distribution breakdown
- Structural instability count and percentage

### 2. LiveFeed Component
**Purpose**: Real-time transaction stream
**Updates**: New row every 1-2 seconds
**Features**:
- Animated highlight for new transactions
- Sortable columns (future enhancement)
- Hover effects on rows
- Connection status indicator
- Comprehensive legend

**Columns**:
1. **Time**: HH:MM:SS format
2. **Sender**: Account ID (cyan)
3. **Receiver**: Account ID (purple)
4. **Amount**: Dollar amount (green)
5. **Risk**: Score badge (color-coded)
6. **Drift**: Deviation value (color-coded)
7. **Flags**: Warning icons
8. **Activity**: Level badge (color-coded)

### 3. GraphViewWrapper Component
**Purpose**: Network graph visualization (existing)
**Status**: Already implemented
**Integration**: Ready for future enhancements

## 🔄 Data Flow

```
MockWebSocket Service
        ↓
    App.jsx (State Management)
        ↓
    ┌───┴────┐
    ↓        ↓
StatsPanel  LiveFeed
```

### Transaction Data Structure
```javascript
// Example transaction object structure
const transaction = {
  id: "abc123",
  timestamp: "2024-01-01T12:00:00Z",
  sender: "acct_0123",
  receiver: "acct_0456",
  amount: "1234.56",
  risk: 75,
  drift: "0.45",
  structuralInstability: false,
  suspicionTrend: "up",
  activityLevel: "medium",
  flagged: false,

  // Additional fields (for future use)
  activity1h: 25,
  activity24h: 300,
  activity7d: 1500,
  transactionType: "transfer",
  region: "US-EAST"
};
```

**Field Descriptions:**
- `id`: Unique identifier
- `timestamp`: ISO timestamp
- `sender`: Sender account
- `receiver`: Receiver account
- `amount`: Transaction amount
- `risk`: Risk score (0-100)
- `drift`: Drift value (-1 to 1)
- `structuralInstability`: Boolean flag
- `suspicionTrend`: "up" or "down"
- `activityLevel`: "low", "medium", "high"
- `flagged`: Auto-flagged if risk > 80

## 🎯 Key Features

### Real-Time Updates
- ✅ New transactions appear at the top
- ✅ Smooth fade-in animation
- ✅ Auto-scroll to show latest
- ✅ Maximum 15 transactions displayed

### Visual Feedback
- ✅ Pulsing green dot when connected
- ✅ Cyan highlight for new transactions
- ✅ Hover effect on table rows
- ✅ Color-coded risk indicators
- ✅ Icon-based warning system

### Responsive Design
- ✅ Works on desktop and tablet
- ✅ Horizontal scroll on mobile
- ✅ Grid layout adapts to screen size
- ✅ Touch-friendly interface

## 🚀 Performance

- **Update Frequency**: 1-2 seconds per transaction
- **Max Transactions**: 15 (prevents memory bloat)
- **Animation Duration**: 1 second highlight
- **Re-render Optimization**: React state batching

## 🔧 Customization Options

### Adjust Update Speed
In `mockWebSocket.js`, change the interval:
```javascript
// Faster updates (0.5-1 second)
1000 + Math.random() * 500

// Slower updates (2-4 seconds)
2000 + Math.random() * 2000
```

### Change Max Transactions
In `App.jsx`, modify the slice:
```javascript
// Show more transactions
setTransactions((prev) => [newTx, ...prev].slice(0, 25));
```

### Adjust Risk Thresholds
In `riskColors.js`, modify the conditions:
```javascript
if (risk > 70) return "bg-red-500/20...";  // More sensitive
if (risk > 60) return "bg-yellow-500/20...";
```

## 📝 Testing Checklist

- [ ] Run `npm run dev` successfully
- [ ] See transactions appearing in real-time
- [ ] Stats panel updates with each transaction
- [ ] Risk colors display correctly (green/yellow/red)
- [ ] Drift values show with correct colors
- [ ] Warning icons appear for structural instability
- [ ] Suspicion trend arrows display
- [ ] Activity level badges show
- [ ] Connection indicator shows "Live"
- [ ] New transaction highlight animation works
- [ ] Hover effects work on table rows
- [ ] Legend displays at bottom

## 🎓 For Your Team

**Person 3 (Monique) - Frontend + WebSocket UI** ✅

You now have:
- ✅ Complete live feed component
- ✅ Risk color mapping
- ✅ Real-time updates (mocked)
- ✅ Statistics dashboard
- ✅ Professional dark theme
- ✅ All advanced metrics visualized
- ✅ Easy WebSocket integration path

**Ready to integrate with backend when available!**
