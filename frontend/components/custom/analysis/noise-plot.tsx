"use client"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts"

export type NoisePoint = {
  freq: number
  noise: number
}

type NoisePlotProps = {
  data: NoisePoint[]
  className?: string
}

export function NoisePlot({ data, className }: NoisePlotProps) {
  return (
    <ChartContainer
      config={{
        noise: { label: "Noise spectral density", color: "#f97316" },
      }}
      className={className ?? "h-[280px]"}
    >
      <LineChart data={data} margin={{ left: 12, right: 12 }}>
        <CartesianGrid strokeDasharray="4 4" />
        <XAxis dataKey="freq" type="number" scale="log" domain={[1, 100000]} />
        <YAxis scale="log" domain={[1e-8, 1e-5]} />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Line type="monotone" dataKey="noise" stroke="var(--color-noise)" strokeWidth={2} dot={false} />
      </LineChart>
    </ChartContainer>
  )
}
