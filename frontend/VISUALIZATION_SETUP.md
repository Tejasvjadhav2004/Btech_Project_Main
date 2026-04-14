# Visualization Setup Guide

This guide explains how to set up the chart libraries and visualizations that have been added to the Supply Chain Management System.

## Overview

The frontend has been enhanced with interactive charts and visualizations using **Recharts**, a composable charting library built on React components.

## Installation

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn package manager

### Install Dependencies

Run the following command in the `frontend` directory:

```bash
npm install recharts
```

Or if using yarn:

```bash
yarn add recharts
```

## What's Been Added

### 1. Chart Library
- **Recharts v2.12.0** - A composable charting library for React

### 2. Updated Pages with Visualizations

#### Dashboard Page (`frontend/src/pages/Dashboard.jsx`)
- **Stock Distribution by Category** - Pie chart showing inventory breakdown
- **Top 10 Products by Revenue** - Bar chart displaying best-performing products
- **Warehouse Utilization & Stock Levels** - Dual-axis bar chart

#### Forecast Page (`frontend/src/pages/Forecast.jsx`)
- **Predicted vs Actual Demand** - Line chart for trend comparison
- **Demand Comparison** - Bar chart side-by-side view
- **Forecast Details Table** - Enhanced with accuracy metrics

#### Intelligence Page (`frontend/src/pages/Intelligence.jsx`)
- **Signals by Severity** - Pie chart showing alert distribution
- **Signals by Type** - Bar chart categorizing signal types
- **Active Signals List** - Maintained with interactive actions

#### Inventory Page (`frontend/src/pages/Inventory.jsx`)
- **Stock Status Distribution** - Pie chart (Low/Normal/Overstock)
- **Stock by Warehouse** - Bar chart showing inventory per location
- **Top 10 Products by Stock Level** - Area chart for high-stock items

#### Orders Page (`frontend/src/pages/Orders.jsx`)
- **Order Status Distribution** - Pie chart showing order states
- **Recent Order Amounts** - Line chart tracking order values

#### Deliveries Page (`frontend/src/pages/Deliveries.jsx`)
- **Delivery Status Distribution** - Pie chart tracking delivery states
- **Distance & Duration Analysis** - Area chart showing delivery metrics

## Chart Types Used

### Pie Chart
- Used for categorical data distribution
- Examples: Stock status, order status, signal severity

### Bar Chart
- Used for comparing values across categories
- Examples: Warehouse utilization, top products, signal types

### Line Chart
- Used for showing trends over time
- Examples: Order amounts, demand forecasts

### Area Chart
- Used for showing volume and trends
- Examples: Stock levels, delivery metrics

## Features

### Responsive Design
All charts use `ResponsiveContainer` to automatically adjust to screen size.

### Interactive Tooltips
Hover over charts to see detailed information with formatted values.

### Color Coding
Charts use consistent color schemes:
- **Blue (#3b82f6)** - Primary metrics
- **Green (#10b981)** - Positive/success indicators
- **Yellow (#f59e0b)** - Warnings/pending states
- **Red (#ef4444)** - Critical/error states
- **Orange (#f97316)** - Medium priority alerts

### Legend Support
All charts include legends for easy identification of data series.

## Troubleshooting

### Charts Not Displaying

1. **Check Dependencies**
   ```bash
   cd frontend
   npm list recharts
   ```

2. **Clear Cache and Reinstall**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Check Console for Errors**
   - Open browser DevTools (F12)
   - Check Console tab for any React or Recharts errors

### Performance Issues

If charts are slow to load:
- Reduce the amount of data displayed
- Use data pagination
- Consider implementing virtual scrolling for large datasets

### Styling Issues

If charts don't match the expected design:
- Ensure all chart components are wrapped in `ResponsiveContainer`
- Check that parent containers have defined heights
- Verify CSS isn't conflicting with chart styles

## Development

### Adding New Charts

To add a chart to a new page:

1. Import chart components:
```javascript
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
```

2. Prepare data in the correct format:
```javascript
const chartData = [
  { name: 'Category 1', value: 100 },
  { name: 'Category 2', value: 200 }
];
```

3. Render the chart:
```javascript
<ResponsiveContainer width="100%" height={300}>
  <BarChart data={chartData}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="name" />
    <YAxis />
    <Tooltip />
    <Legend />
    <Bar dataKey="value" fill="#3b82f6" />
  </BarChart>
</ResponsiveContainer>
```

## Best Practices

1. **Always use ResponsiveContainer** for responsive design
2. **Provide meaningful labels** for axes and legends
3. **Use consistent colors** across the application
4. **Format data appropriately** (currency, percentages, etc.)
5. **Handle empty states** gracefully when no data is available
6. **Keep charts simple** - avoid overcrowding with too much data

## Future Enhancements

Potential improvements to consider:

- Real-time data streaming with WebSocket integration
- Export charts as PNG/SVG for reports
- Advanced filtering and drill-down capabilities
- Custom chart themes and color schemes
- Animated transitions between data states
- Mobile-optimized chart layouts

## Support

For issues or questions:
- Check the [Recharts documentation](https://recharts.org/)
- Review the project's main README.md
- Open an issue in the project repository

---

**Note:** Make sure to run `npm install` in the frontend directory after pulling these changes to ensure all dependencies are properly installed.