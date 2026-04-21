"use client"

import {
  ChartContainer,
  ChartLegend,
  ChartLegendContent,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  ReferenceLine,
} from "recharts"

export type TransientPoint = {
  time: number
  vin: number
  vout: number
}

type TransientWaveformPlotProps = {
  data: TransientPoint[]
  markers?: Array<{ time: number; color?: string }>
  className?: string
}

export function TransientWaveformPlot({
  data,
  markers = [],
  className,
}: TransientWaveformPlotProps) {
  return (
    <ChartContainer
      config={{
        vout: { label: "Vout", color: "#f97316" },
        vin: { label: "Vin", color: "#0ea5e9" },
      }}
      className={className ?? "h-[280px]"}
    >
      <LineChart data={data} margin={{ left: 12, right: 12 }}>
        <CartesianGrid strokeDasharray="4 4" />
        <XAxis dataKey="time" type="number" />
        <YAxis />
        <ChartTooltip content={<ChartTooltipContent />} />
        <ChartLegend content={<ChartLegendContent />} />
        {markers.map((marker, index) => (
          <ReferenceLine
            key={`${marker.time}-${index}`}
            x={marker.time}
            stroke={marker.color ?? "#f97316"}
            strokeDasharray="4 4"
          />
        ))}
        <Line type="monotone" dataKey="vout" stroke="var(--color-vout)" strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="vin" stroke="var(--color-vin)" strokeWidth={2} dot={false} />
      </LineChart>
    </ChartContainer>
  )
}
