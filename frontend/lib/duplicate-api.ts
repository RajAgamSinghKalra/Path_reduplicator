const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export interface DuplicateCheckRequest {
  full_name: string
  date_of_birth: string
  phone: string
  email: string
  government_id: string
  address_line: string
  city: string
  state: string
  postal_code: string
  country: string
}

export interface BestMatch {
  name: string
  date_of_birth: string
  phone: string
  email: string
  government_id: string
  address_line: string
  city: string
  state: string
  postal_code: string
  country: string
  score: number
  vector_distance: number
}

export interface CandidateMatch {
  customer_id: string
  name: string
  date_of_birth: string
  phone: string
  email: string
  government_id: string
  address_line: string
  city: string
  state: string
  postal_code: string
  country: string
  score: number
  vector_distance: number
}

export interface DuplicateCheckResponse {
  is_duplicate: boolean
  score: number
  best_match: BestMatch | null
  candidates: CandidateMatch[]
  threshold: number
}

export interface DuplicateCheckResult {
  success: boolean
  message?: string
  data?: DuplicateCheckResponse
}

export async function checkDuplicate(request: DuplicateCheckRequest): Promise<DuplicateCheckResult> {
  try {
    const response = await fetch(`${API_BASE_URL}/dedupe/check`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
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
