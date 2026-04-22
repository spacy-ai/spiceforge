export type AnalysisResult = {
  analysis?: string
  data?: Record<string, unknown>
  measurements?: Record<string, unknown>
  warnings?: string[]
}

export type SimulationError = {
  message?: string
  hint?: string
  code?: string
}

export type SimulationResponse = {
  status: string
  analyses?: string[]
  results?: AnalysisResult[]
  circuit_type?: string
  schematic?: {
    content?: string
  }
  error?: SimulationError
}
