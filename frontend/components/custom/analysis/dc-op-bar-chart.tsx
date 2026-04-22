"use client"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from "recharts"

export type DcOpPoint = {
  node: string
  voltage: number
}

type DcOpBarChartProps = {
  data: DcOpPoint[]
  className?: string
}

export function DcOpBarChart({ data, className }: DcOpBarChartProps) {
  return (
    <ChartContainer
      config={{
        voltage: { label: "Node voltage", color: "#f97316" },
      }}
      className={className ?? "h-[280px]"}
    >
      <BarChart data={data} margin={{ left: 12, right: 12 }}>
        <CartesianGrid strokeDasharray="4 4" />
        <XAxis dataKey="node" />
        <YAxis />
        <ChartTooltip content={<ChartTooltipContent />} />
        <Bar dataKey="voltage" fill="var(--color-voltage)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ChartContainer>
  )
}
