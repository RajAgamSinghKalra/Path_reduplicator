export interface LoanDuplicateCheckRequest {
  // Identity fields (sent to API)
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
  // Loan fields (client-side for now)
  account_number: string
  loan_application_id: string
  requested_amount: string
  loan_type: string
  branch_code: string
}

export interface LoanCandidateMatch {
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
  score: number
  vector_distance: number
  // Enhanced loan information
  existing_account_id?: string
  existing_loan_ids?: string[]
  loan_history?: {
    loan_type: string
    amount: number
    status: string
    date: string
  }[]
}

export interface LoanDuplicateCheckResponse {
  is_duplicate: boolean
  score: number
  threshold: number
  best_match: LoanCandidateMatch | null
  candidates: LoanCandidateMatch[]
}

export interface ApiResponse {
  success: boolean
  message: string
  data?: LoanDuplicateCheckResponse
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export const checkLoanDuplicate = async (formData: LoanDuplicateCheckRequest): Promise<ApiResponse> => {
  try {
    // Extract only identity fields for API submission
    const identityData = {
      full_name: formData.full_name,
      date_of_birth: formData.date_of_birth,
      phone: formData.phone,
      email: formData.email,
      government_id: formData.government_id,
      address_line: formData.address_line,
      city: formData.city,
      state: formData.state,
      postal_code: formData.postal_code,
      country: formData.country,
    }

    const response = await fetch(`${API_BASE_URL}/dedupe/check`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(identityData),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
    }

    const data: LoanDuplicateCheckResponse = await response.json()

    return {
      success: true,
      message: "Duplicate check completed successfully",
      data,
    }
  } catch (error) {
    console.error("Error checking for duplicates:", error)
    return {
      success: false,
      message: error instanceof Error ? error.message : "Failed to check for duplicates",
    }
  }
}
