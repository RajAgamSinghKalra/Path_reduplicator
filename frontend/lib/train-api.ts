const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export interface TrainModelRequest {
  data_path: string
}

export interface TrainModelResponse {
  success: boolean
  message: string
  training_id?: string
  status?: string
  details?: {
    pairs_processed?: number
    accuracy?: number
    training_time?: number
  }
}

export interface TrainModelResult {
  success: boolean
  message?: string
  data?: TrainModelResponse
}

export async function trainModel(request: TrainModelRequest): Promise<TrainModelResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/train`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ csv_path: request.data_path }),
    })

    const data = await response.json()

    if (response.ok) {
      return {
        success: true,
        data: data,
      }
    } else {
      return {
        success: false,
        message: data.message || `HTTP ${response.status}: ${response.statusText}`,
      }
    }
  } catch (error) {
    return {
      success: false,
      message: error instanceof Error ? error.message : "Network error occurred",
    }
  }
}
