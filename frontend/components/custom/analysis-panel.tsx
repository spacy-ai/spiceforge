"use client"

import { useMemo, useState } from "react"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import {
  Field,
  FieldContent,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldTitle,
} from "@/components/ui/field"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { RotateCcw } from "lucide-react"
import type { SimulationResponse } from "@/lib/types/simulation"
import { AcBodePlot } from "@/components/custom/analysis/ac-bode-plot"
import { TransientWaveformPlot } from "@/components/custom/analysis/transient-waveform-plot"
import { DcSweepPlot } from "@/components/custom/analysis/dc-sweep-plot"
import { NoisePlot } from "@/components/custom/analysis/noise-plot"
import { DcOpBarChart } from "@/components/custom/analysis/dc-op-bar-chart"

type AnalysisType = "ac" | "transient" | "dc-op" | "dc-sweep" | "noise"
type CircuitType = "generic" | "amplifier" | "filter" | "oscillator"

type AnalysisPanelProps = {
  simulation?: SimulationResponse | null
}

const acData = [
  { freq: 10, mag: -2.5, phase: -5 },
  { freq: 30, mag: -1.2, phase: -15 },
  { freq: 100, mag: 0, phase: -30 },
  { freq: 300, mag: 3.2, phase: -55 },
  { freq: 1000, mag: 3.1, phase: -85 },
  { freq: 3000, mag: 1.2, phase: -120 },
  { freq: 10000, mag: -3.1, phase: -160 },
  { freq: 30000, mag: -8.5, phase: -175 },
  { freq: 100000, mag: -15.2, phase: -178 },
]

const transientData = [
  { time: 0, vin: 0, vout: 0 },
  { time: 0.001, vin: 0.6, vout: 0.2 },
  { time: 0.002, vin: 1.2, vout: 0.7 },
  { time: 0.003, vin: 1.2, vout: 1.05 },
  { time: 0.004, vin: 1.2, vout: 1.18 },
  { time: 0.005, vin: 1.2, vout: 1.12 },
  { time: 0.006, vin: 1.2, vout: 1.16 },
  { time: 0.007, vin: 1.2, vout: 1.15 },
]

const dcSweepData = [
  { sweep: 0, vout: 0.05 },
  { sweep: 0.5, vout: 0.42 },
  { sweep: 1, vout: 0.85 },
  { sweep: 1.5, vout: 1.27 },
  { sweep: 2, vout: 1.69 },
  { sweep: 2.5, vout: 2.08 },
  { sweep: 3, vout: 2.38 },
  { sweep: 3.5, vout: 2.55 },
]

const noiseData = [
  { freq: 1, noise: 1.2e-6 },
  { freq: 10, noise: 8.5e-7 },
  { freq: 100, noise: 3.1e-7 },
  { freq: 1000, noise: 1.4e-7 },
  { freq: 10000, noise: 7.2e-8 },
  { freq: 100000, noise: 3.8e-8 },
]

const dcOpData = [
  { node: "Vout", voltage: 1.2 },
  { node: "Vref", voltage: 0.6 },
  { node: "Vbias", voltage: 0.3 },
  { node: "Vdd", voltage: 3.3 },
]

const defaultMetrics: Record<AnalysisType, Array<{ label: string; value: string }>> = {
  ac: [
    { label: "-3 dB cutoff", value: "12.4 kHz" },
    { label: "Midband gain", value: "3.1 dB" },
    { label: "Rolloff rate", value: "-20 dB/dec" },
    { label: "Phase @ 1 kHz", value: "-85 deg" },
  ],
  transient: [
    { label: "Rise time", value: "2.1 ms" },
    { label: "Settling time", value: "6.0 ms" },
    { label: "Overshoot", value: "6.5 %" },
    { label: "Peak voltage", value: "1.18 V" },
  ],
  "dc-op": [
    { label: "Total power", value: "18.2 mW" },
    { label: "Vout", value: "1.20 V" },
    { label: "Dominant node", value: "Vdd" },
    { label: "Bias current", value: "2.8 mA" },
  ],
  "dc-sweep": [
    { label: "Gain region", value: "0.8 to 2.6 V" },
    { label: "Slope", value: "0.82 V/V" },
    { label: "Saturation", value: "2.55 V" },
    { label: "Knee point", value: "2.1 V" },
  ],
  noise: [
    { label: "Input noise", value: "1.2 uV/rtHz" },
    { label: "Output noise", value: "8.4 uV/rtHz" },
    { label: "Bandwidth", value: "120 kHz" },
    { label: "Noise figure", value: "2.1 dB" },
  ],
}

const circuitActions: Record<CircuitType, Array<{ label: string; rerun?: boolean; inline?: boolean }>> = {
  amplifier: [
    { label: "Gain at custom frequency", inline: true },
    { label: "Phase margin", inline: false },
    { label: "Gain sweep across decades", rerun: true },
  ],
  filter: [
    { label: "Stopband attenuation", inline: false },
    { label: "Passband ripple", inline: false },
    { label: "Group delay", inline: false },
  ],
  oscillator: [
    { label: "Oscillation frequency", inline: false },
    { label: "THD", inline: false },
    { label: "Startup time", inline: false },
  ],
  generic: [
    { label: "Peak value", inline: false },
    { label: "Min value", inline: false },
  ],
}

const errorList = (message?: string) => (message ? [{ message }] : undefined)

const normalizeCircuitType = (value?: string | null): CircuitType => {
  if (!value) return "generic"
  const normalized = value.trim().toLowerCase()
  if (normalized === "amplifier" || normalized === "amp") return "amplifier"
  if (normalized === "filter") return "filter"
  if (normalized === "oscillator" || normalized === "osc") return "oscillator"
  if (normalized === "generic") return "generic"
  return "generic"
}

const analysisTabs: Array<{ value: AnalysisType; label: string }> = [
  { value: "ac", label: "AC" },
  { value: "transient", label: "Transient" },
  { value: "dc-op", label: "DC OP" },
  { value: "dc-sweep", label: "DC Sweep" },
  { value: "noise", label: "Noise" },
]

export function AnalysisPanel({ simulation }: AnalysisPanelProps) {
  const [analysisType, setAnalysisType] = useState<AnalysisType>("ac")
  const [hasResults, setHasResults] = useState(false)
  const [activeAction, setActiveAction] = useState<string | null>(null)
  const [errors, setErrors] = useState<Record<string, string>>({})

  const circuitType = useMemo(
    () => normalizeCircuitType(simulation?.circuit_type),
    [simulation?.circuit_type],
  )

  const [acForm, setAcForm] = useState({
    startFreq: "10",
    stopFreq: "100000",
    pointsPerDecade: "50",
  })
  const [transientForm, setTransientForm] = useState({
    stopTime: "0.01",
    stepTime: "0.000001",
    startupTime: "",
  })
  const [dcOpForm, setDcOpForm] = useState({ nodeName: "Vout" })
  const [dcSweepForm, setDcSweepForm] = useState({
    sourceName: "V1",
    start: "0",
    stop: "3.5",
    step: "0.1",
  })
  const [noiseForm, setNoiseForm] = useState({
    startFreq: "1",
    stopFreq: "100000",
    outputNode: "Vout",
  })

  const measurementEntries = useMemo(() => {
    const results = simulation?.results ?? []
    return results.flatMap((result, index) => {
      const measurements = result.measurements ?? {}
      return Object.entries(measurements).map(([key, value]) => ({
        key,
        value,
        analysis: result.analysis || `Result ${index + 1}`,
      }))
    })
  }, [simulation])

  const summaryMetrics = useMemo(() => {
    if (measurementEntries.length) {
      return measurementEntries.slice(0, 4).map((entry) => ({
        label: entry.key,
        value: String(entry.value),
      }))
    }
    return defaultMetrics[analysisType]
  }, [analysisType, measurementEntries])

  const validate = () => {
    const nextErrors: Record<string, string> = {}

    if (analysisType === "ac") {
      const startFreq = Number(acForm.startFreq)
      const stopFreq = Number(acForm.stopFreq)
      const points = Number(acForm.pointsPerDecade)

      if (!startFreq || startFreq <= 0) {
        nextErrors.acStartFreq = "Start frequency must be greater than 0"
      }
      if (!stopFreq || stopFreq <= 0) {
        nextErrors.acStopFreq = "Stop frequency must be greater than 0"
      }
      if (stopFreq && startFreq && stopFreq <= startFreq) {
        nextErrors.acStopFreq = "Stop frequency must be greater than start frequency"
      }
      if (!points || points <= 0) {
        nextErrors.acPoints = "Points per decade must be greater than 0"
      }
    }

    if (analysisType === "transient") {
      const stopTime = Number(transientForm.stopTime)
      const stepTime = Number(transientForm.stepTime)
      if (!stopTime || stopTime <= 0) {
        nextErrors.trStopTime = "Stop time must be greater than 0"
      }
      if (!stepTime || stepTime <= 0) {
        nextErrors.trStepTime = "Step time must be greater than 0"
      }
      if (stopTime > 0 && stepTime > 0) {
        const points = stopTime / stepTime
        if (points > 1000000) {
          nextErrors.trStepTime = "Step time produces more than 1,000,000 points"
        }
      }
    }

    if (analysisType === "dc-op") {
      if (!dcOpForm.nodeName.trim()) {
        nextErrors.dcOpNode = "Node name is required"
      }
    }

    if (analysisType === "dc-sweep") {
      const start = Number(dcSweepForm.start)
      const stop = Number(dcSweepForm.stop)
      const step = Number(dcSweepForm.step)
      if (!dcSweepForm.sourceName.trim()) {
        nextErrors.dcSweepSource = "Source name is required"
      }
      if (!step || step <= 0) {
        nextErrors.dcSweepStep = "Step size must be greater than 0"
      }
      if (stop <= start) {
        nextErrors.dcSweepStop = "Stop value must be greater than start value"
      }
    }

    if (analysisType === "noise") {
      const start = Number(noiseForm.startFreq)
      const stop = Number(noiseForm.stopFreq)
      if (!start || start <= 0) {
        nextErrors.noiseStart = "Start frequency must be greater than 0"
      }
      if (!stop || stop <= 0) {
        nextErrors.noiseStop = "Stop frequency must be greater than 0"
      }
      if (stop && start && stop <= start) {
        nextErrors.noiseStop = "Stop frequency must be greater than start frequency"
      }
    }

    setErrors(nextErrors)
    return Object.keys(nextErrors).length === 0
  }

  const handleRun = () => {
    if (!validate()) return
    setHasResults(true)
    setActiveAction(null)
  }

  return (
    <div className="flex h-full flex-col bg-background">
      <div className="border-b border-border px-4 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-foreground">Simulation Analysis</h2>
            <p className="text-xs text-muted-foreground">Configure the run and review post-simulation insights.</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">Analysis: {analysisType.toUpperCase()}</Badge>
            <Badge variant="secondary">Circuit: {circuitType}</Badge>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 pb-6 pt-4">
        <Tabs
          value={analysisType}
          onValueChange={(value) => {
            setAnalysisType(value as AnalysisType)
            setHasResults(false)
            setErrors({})
            setActiveAction(null)
          }}
        >
          <TabsList className="mb-4">
            {analysisTabs.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>

          <div className="rounded-lg border border-border bg-card p-4">
            <FieldGroup className="gap-4">
              <FieldTitle>Input panel</FieldTitle>
              <TabsContent value="ac">
                <div className="grid gap-4 md:grid-cols-3">
                  <Field>
                    <FieldLabel htmlFor="ac-start">Start frequency (Hz)</FieldLabel>
                    <FieldContent>
                      <Input
                        id="ac-start"
                        value={acForm.startFreq}
                        onChange={(e) => setAcForm((prev) => ({ ...prev, startFreq: e.target.value }))}
                      />
                      <FieldError errors={errorList(errors.acStartFreq)} />
                    </FieldContent>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="ac-stop">Stop frequency (Hz)</FieldLabel>
                    <FieldContent>
                      <Input
                        id="ac-stop"
                        value={acForm.stopFreq}
                        onChange={(e) => setAcForm((prev) => ({ ...prev, stopFreq: e.target.value }))}
                      />
                      <FieldError errors={errorList(errors.acStopFreq)} />
                    </FieldContent>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="ac-points">Points per decade</FieldLabel>
                    <FieldContent>
                      <Input
                        id="ac-points"
                        value={acForm.pointsPerDecade}
                        onChange={(e) => setAcForm((prev) => ({ ...prev, pointsPerDecade: e.target.value }))}
                      />
                      <FieldError errors={errorList(errors.acPoints)} />
                    </FieldContent>
                  </Field>
                </div>
              </TabsContent>

              <TabsContent value="transient">
                <div className="grid gap-4 md:grid-cols-3">
                  <Field>
                    <FieldLabel htmlFor="tr-stop">Stop time (s)</FieldLabel>
                    <FieldContent>
                      <Input
                        id="tr-stop"
                        value={transientForm.stopTime}
                        onChange={(e) => setTransientForm((prev) => ({ ...prev, stopTime: e.target.value }))}
                      />
                      <FieldError errors={errorList(errors.trStopTime)} />
                    </FieldContent>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="tr-step">Step time (s)</FieldLabel>
                    <FieldContent>
                      <Input
                        id="tr-step"
                        value={transientForm.stepTime}
                        onChange={(e) => setTransientForm((prev) => ({ ...prev, stepTime: e.target.value }))}
                      />
                      <FieldError errors={errorList(errors.trStepTime)} />
                    </FieldContent>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="tr-startup">Startup time (s) (optional)</FieldLabel>
                    <FieldContent>
                      <Input
                        id="tr-startup"
                        value={transientForm.startupTime}
                        onChange={(e) => setTransientForm((prev) => ({ ...prev, startupTime: e.target.value }))}
                      />
                    </FieldContent>
                  </Field>
                </div>
              </TabsContent>

              <TabsContent value="dc-op">
                <div className="grid gap-4 md:grid-cols-2">
                  <Field>
                    <FieldLabel htmlFor="dcop-node">Node name to probe</FieldLabel>
                    <FieldContent>
                      <Input
                        id="dcop-node"
                        value={dcOpForm.nodeName}
                        onChange={(e) => setDcOpForm({ nodeName: e.target.value })}
                      />
                      <FieldError errors={errorList(errors.dcOpNode)} />
                    </FieldContent>
                  </Field>
                </div>
              </TabsContent>

              <TabsContent value="dc-sweep">
                <div className="grid gap-4 md:grid-cols-4">
                  <Field>
                    <FieldLabel htmlFor="dcs-source">Source name</FieldLabel>
                    <FieldContent>
                      <Input
                        id="dcs-source"
                        value={dcSweepForm.sourceName}
                        onChange={(e) => setDcSweepForm((prev) => ({ ...prev, sourceName: e.target.value }))}
                      />
                      <FieldError errors={errorList(errors.dcSweepSource)} />
                    </FieldContent>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="dcs-start">Start</FieldLabel>
                    <FieldContent>
                      <Input
                        id="dcs-start"
                        value={dcSweepForm.start}
                        onChange={(e) => setDcSweepForm((prev) => ({ ...prev, start: e.target.value }))}
                      />
                    </FieldContent>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="dcs-stop">Stop</FieldLabel>
                    <FieldContent>
                      <Input
                        id="dcs-stop"
                        value={dcSweepForm.stop}
                        onChange={(e) => setDcSweepForm((prev) => ({ ...prev, stop: e.target.value }))}
                      />
                      <FieldError errors={errorList(errors.dcSweepStop)} />
                    </FieldContent>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="dcs-step">Step</FieldLabel>
                    <FieldContent>
                      <Input
                        id="dcs-step"
                        value={dcSweepForm.step}
                        onChange={(e) => setDcSweepForm((prev) => ({ ...prev, step: e.target.value }))}
                      />
                      <FieldError errors={errorList(errors.dcSweepStep)} />
                    </FieldContent>
                  </Field>
                </div>
              </TabsContent>

              <TabsContent value="noise">
                <div className="grid gap-4 md:grid-cols-3">
                  <Field>
                    <FieldLabel htmlFor="noise-start">Start frequency (Hz)</FieldLabel>
                    <FieldContent>
                      <Input
                        id="noise-start"
                        value={noiseForm.startFreq}
                        onChange={(e) => setNoiseForm((prev) => ({ ...prev, startFreq: e.target.value }))}
                      />
                      <FieldError errors={errorList(errors.noiseStart)} />
                    </FieldContent>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="noise-stop">Stop frequency (Hz)</FieldLabel>
                    <FieldContent>
                      <Input
                        id="noise-stop"
                        value={noiseForm.stopFreq}
                        onChange={(e) => setNoiseForm((prev) => ({ ...prev, stopFreq: e.target.value }))}
                      />
                      <FieldError errors={errorList(errors.noiseStop)} />
                    </FieldContent>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="noise-out">Output node</FieldLabel>
                    <FieldContent>
                      <Input
                        id="noise-out"
                        value={noiseForm.outputNode}
                        onChange={(e) => setNoiseForm((prev) => ({ ...prev, outputNode: e.target.value }))}
                      />
                    </FieldContent>
                  </Field>
                </div>
              </TabsContent>

              <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>Inline validation is active for frequency, time, and point limits.</span>
                </div>
                <Button onClick={handleRun} className="min-w-[150px]">
                  Run analysis
                </Button>
              </div>
            </FieldGroup>
          </div>
        </Tabs>

        {hasResults && (
          <div className="mt-6 space-y-6">
            <div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Summary metrics</h3>
                  <p className="text-xs text-muted-foreground">Auto-measured numbers from the last run.</p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{analysisType.toUpperCase()}</Badge>
                  <Badge variant="secondary">{circuitType}</Badge>
                </div>
              </div>
              <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                {summaryMetrics.map((metric) => (
                  <Card key={metric.label} className="py-4">
                    <CardContent className="space-y-1">
                      <p className="text-xs text-muted-foreground">{metric.label}</p>
                      <p className="text-lg font-semibold text-foreground">{metric.value}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-foreground">Graphs</h3>
              <div className="mt-3 rounded-lg border border-border bg-card p-4">
                {analysisType === "ac" && (
                  <AcBodePlot data={acData} />
                )}

                {analysisType === "transient" && (
                  <TransientWaveformPlot
                    data={transientData}
                    markers={[
                      { time: 0.002, color: "#f97316" },
                      { time: 0.006, color: "#0ea5e9" },
                    ]}
                  />
                )}

                {analysisType === "dc-sweep" && (
                  <DcSweepPlot data={dcSweepData} />
                )}

                {analysisType === "noise" && (
                  <NoisePlot data={noiseData} />
                )}

                {analysisType === "dc-op" && (
                  <DcOpBarChart data={dcOpData} />
                )}
              </div>
            </div>

            {measurementEntries.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-foreground">Measurements from backend</h3>
                <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  {measurementEntries.map((entry) => (
                    <Card key={`${entry.analysis}-${entry.key}`} className="py-3">
                      <CardContent className="space-y-1">
                        <p className="text-xs text-muted-foreground">{entry.analysis}</p>
                        <p className="text-sm font-medium text-foreground">{entry.key}</p>
                        <p className="text-base font-semibold text-foreground">{String(entry.value)}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            <div>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Next actions</h3>
                  <p className="text-xs text-muted-foreground">Compute additional insights without re-running.</p>
                </div>
                <Badge variant="outline">Source: backend</Badge>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {circuitActions[circuitType].map((action) => (
                  <Button
                    key={action.label}
                    variant="secondary"
                    size="sm"
                    className="gap-2"
                    onClick={() => setActiveAction(action.inline ? action.label : null)}
                  >
                    {action.rerun && <RotateCcw className="h-3 w-3" />}
                    {action.label}
                  </Button>
                ))}
              </div>
              {activeAction && (
                <div className="mt-3 rounded-lg border border-border bg-card p-3">
                  <p className="text-xs text-muted-foreground">{activeAction}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <Input placeholder="Enter frequency (Hz)" className="max-w-[200px]" />
                    <Button size="sm">Compute</Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}