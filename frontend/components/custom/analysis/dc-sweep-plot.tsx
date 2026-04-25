'use client';

import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { LineChart, Line, XAxis, YAxis, CartesianGrid } from 'recharts';

export type DcSweepPoint = {
  sweep: number;
  vout: number;
};

type DcSweepPlotProps = {
  data: DcSweepPoint[];
  className?: string;
};

export function DcSweepPlot({ data, className }: DcSweepPlotProps) {
  return (
    <ChartContainer
      config={{
        vout: { label: 'Vout', color: '#f97316' },
      }}
      className={className ?? 'h-[280px]'}
    >
      <LineChart data={data} margin={{ left: 12, right: 12 }}>
        <CartesianGrid strokeDasharray="4 4" />
        <XAxis dataKey="sweep" type="number" />
        <YAxis />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Line
          type="monotone"
          dataKey="vout"
          stroke="var(--color-vout)"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ChartContainer>
  );
}
