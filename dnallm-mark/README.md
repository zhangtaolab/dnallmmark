# DNALLM Mark - Local Clone


## 🎯 Project Overview

This is a locally implemented AI model leaderboard website, built with pure HTML, CSS, and JavaScript, maintaining the original website's design style and core functionality.

## ✨ Features

### Implemented Features ✅

- ✅ **Precise Design System**: CSS variables, colors, fonts, and layouts extracted directly from the source code
- ✅ **Responsive Navigation Bar**: Contains Logo, navigation links, and social buttons
- ✅ **Hero Section**: Main title and subtitle
- ✅ **Category Tab Navigation**: 19 arena categories (All Categories, Website, Web App, etc.)
- ✅ **Scatter Plot**: Visualizes model performance (Elo Rating) vs. generation time
- ✅ **Leaderboard Table**: Displays model ranking, name, Elo rating, win rate, and battle count
- ✅ **Filtering Function**: Top 20 / Top 10 filtering
- ✅ **Sorting Function**: Sort by Rank, Name, Elo Rating, Win Rate, Battles
- ✅ **Interactive Effects**: Hover states, click feedback, transition animations
- ✅ **Progress Bar**: Visualizes win rate display
- ✅ **Ranking Badges**: Top three special styles (gold, silver, bronze gradient)

### Pending Features ⏳

- ⏳ Search Function: Model name search
- ⏳ Mobile Full Adaptation: Optimize small screen experience
- ⏳ Dark Mode: Theme switching functionality
- ⏳ Data Persistence: Load data from JSON files or API
- ⏳ Historical Rankings: View historical data changes

## 🚀 Quick Start

### Local Running

1. **Navigate to project directory**


2. **Start local server**
   ```bash
   # Using Python
   python3 -m http.server 8000
   
   # Or using Node.js
   npx serve .
   ```

3. **Access the application**
   - Open browser and visit: `http://localhost:8000`
   - Or simply double-click `index.html` file

## 📁 Project Structure

```
design-arena-local/
├── index.html              # Main page
├── README.md               # Project documentation
├── css/
│   ├── variables.css      # CSS variable system (precise values)
│   ├── reset.css          # Reset styles
│   ├── typography.css     # Typography system
│   ├── layout.css         # Layout styles
│   ├── components.css     # Component styles
│   ├── charts.css         # Chart styles
│   └── styles.css         # Main styles entry point
├── js/
│   ├── config.js          # Configuration file
│   ├── data.js            # Sample data
│   └── main.js            # Main logic
└── assets/                # Static assets (reserved)
```

## 🎨 Design System

### Color System

All color values extracted directly from Design Arena source code:

```css
--color-primary: #292C33;        /* Dark gray - primary text */
--color-bg-cream: #F7F6F5;        /* Cream white - secondary background */
--color-accent-teal: #265354;     /* Teal green - accent color */
--color-success: #52C41A;        /* Green - progress bar */
--color-border: #D9D9D9;         /* Light gray - border */
```

### Font System

- **Display Font**: system-ui (alternative to Concrette)
- **Body Font**: Inter (with system-ui fallback)
- **Font Size Range**: 11px - 40px

### Responsive Breakpoints

- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

## 🔧 Configuration

### Modify Application Name

Edit `APP_NAME` in `js/config.js`:

```javascript
const CONFIG = {
  APP_NAME: 'DNALLM Mark',
  // ...
};
```

### Modify Arena Categories

Edit `ARENAS` array in `js/config.js`:

```javascript
ARENAS: [
  { id: 'all', name: 'All Categories', icon: '🏆' },
  { id: 'website', name: 'Website', icon: '🌐' },
  // Add more categories...
]
```

### Modify Model Data

Edit `MODELS` array in `js/data.js`:

```javascript
const MODELS = [
  {
    id: 'model-id',
    name: 'Model Name',
    version: '1.0',
    organization: 'Organization',
    elo: 1500,
    winRate: 60.0,
    battles: 1000,
    confidence: 1.0,
    color: '#FFFFFF',
    icon: 'M',
    arenas: ['website', 'webapp'],
    generationTime: 1.0
  }
];
```

### Adjust Table Configuration

Edit `TABLE_CONFIG` in `js/config.js`:

```javascript
TABLE_CONFIG: {
  ROWS_PER_PAGE: 20,
  DEFAULT_SORT: 'elo',
  DEFAULT_FILTER: 'top-20'
}
```

## 🎯 Feature Usage

### Viewing Scatter Plot

1. Open application: http://localhost:8000
2. Scatter plot is located above the leaderboard
3. X-axis: Generation Time (longer to the right means slower)
4. Y-axis: ELO Rating (higher means better performance)
5. Hover over data points to view detailed information

### Switching Arena Categories

Click category tabs at the top to switch between different arenas:
- **All Categories**: View all models
- **Website**: Website design capability
- **Web App**: Web application development
- **Agent**: AI agent performance
- And more...

### Filtering Model Count

Use the filter buttons above the leaderboard:
- **Top 20**: Show top 20
- **Top 10**: Show top 10
- **All Models**: Show all models

### Sorting Data

Click table headers to sort by the following fields:
- **Rank**: Ranking
- **Model**: Model name
- **Elo Rating**: Elo score
- **Win Rate**: Win rate
- **Battles**: Battle count

## 📊 Data Description

Currently using sample data (10 models), including:
- Claude 3 Series (Opus, Sonnet, Haiku)
- GPT-4 Series (4, 4 Turbo, 4o)
- Gemini 3 Series (Pro, Flash)
- DeepSeek R1
- GLM 4.5

### Elo Rating System

Calculated using Bradley-Terry model:
- Higher score means stronger performance
- Based on real user votes
- Dynamically updated

### Generation Time Data

Each model includes generation time (in minutes):
- Fast models: < 1.0m
- Balanced models: 1.0m - 1.5m
- Slow models: > 1.5m

## 🌐 Browser Compatibility

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

## 🚧 Known Issues

1. **Mobile Optimization**: Imperfect experience on screens smaller than 768px
2. **Search Function**: Currently does not support model name search
3. **Data Persistence**: Data is hardcoded in JavaScript

## 🔮 Future Plans

- [ ] Implement search function
- [ ] Optimize mobile experience
- [ ] Implement dark mode
- [ ] Support loading data from JSON files
- [ ] Add historical ranking view feature
- [ ] Implement export function (CSV/JSON)
- [ ] Add sharing feature

## 🤝 Contributing

Welcome to submit Issues and Pull Requests!

## 📄 License

MIT License

## 🙏 Acknowledgments

- Built with pure frontend technology (no frameworks)
- Chart Library: [Chart.js](https://www.chartjs.org/)

---

**Development Status**: 🚀 Active Development

**Last Updated**: 2026-01-15
