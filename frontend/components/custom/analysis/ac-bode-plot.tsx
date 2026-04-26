'use client';

import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart';
import { LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';

export type AcBodePoint = {
  freq: number;
  mag: number;
  phase: number;
};

type AcBodePlotProps = {
  data: AcBodePoint[];
  className?: string;
};

export function AcBodePlot({ data, className }: AcBodePlotProps) {
  return (
    <ChartContainer
      config={{
        mag: { label: 'Magnitude (dB)', color: '#f97316' },
        phase: { label: 'Phase (deg)', color: '#0ea5e9' },
      }}
      className={className ?? 'h-[280px]'}
    >
      <LineChart data={data} margin={{ left: 12, right: 12 }}>
        <CartesianGrid strokeDasharray="4 4" />
        <XAxis
          dataKey="freq"
          type="number"
          scale="log"
          domain={[10, 100000]}
          tickFormatter={(value) => `${value}`}
        />
        <YAxis yAxisId="left" />
        <YAxis yAxisId="right" orientation="right" />
        <ChartTooltip content={<ChartTooltipContent />} />
        <ChartLegend content={<ChartLegendContent />} />
        <Line
          yAxisId="left"
          type="monotone"
          dataKey="mag"
          stroke="var(--color-mag)"
          strokeWidth={2}
          dot={false}
        />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="phase"
          stroke="var(--color-phase)"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ChartContainer>
  );
}
