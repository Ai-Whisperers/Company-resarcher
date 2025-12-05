import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface MetricPoint {
  timestamp: string;
  tokens: number;
  cost: number;
}

interface MetricsChartProps {
  data: MetricPoint[];
}

export function MetricsChart({ data }: MetricsChartProps) {
  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle>Resource Usage Over Time</CardTitle>
      </CardHeader>
      <CardContent className="h-[300px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="timestamp" 
              tickFormatter={(time) => new Date(time).toLocaleTimeString()}
            />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip 
              labelFormatter={(label) => new Date(label).toLocaleString()}
            />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="tokens" 
              stroke="#8884d8" 
              name="Tokens"
            />
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="cost" 
              stroke="#82ca9d" 
              name="Cost ($)"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
