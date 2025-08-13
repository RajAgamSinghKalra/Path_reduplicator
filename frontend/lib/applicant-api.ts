export interface ApplicantFormData {
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

export interface ApiResponse {
  success: boolean
  message: string
  data?: any
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export const validateEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export const validateE164Phone = (phone: string): boolean => {
  const e164Regex = /^\+[1-9]\d{1,14}$/
  return e164Regex.test(phone)
}

export const validatePostalCode = (postalCode: string): boolean => {
  const postalRegex = /^\d{6}$/
  return postalRegex.test(postalCode)
}

export const validateDateOfBirth = (date: string): boolean => {
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/
  if (!dateRegex.test(date)) return false

  const parsedDate = new Date(date)
  return parsedDate instanceof Date && !isNaN(parsedDate.getTime())
}

export const validateNumericAmount = (amount: string): boolean => {
  const numericRegex = /^\d+(\.\d{1,2})?$/
  return numericRegex.test(amount) && Number.parseFloat(amount) > 0
}

export const onboardApplicant = async (formData: ApplicantFormData): Promise<ApiResponse> => {
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

    const response = await fetch(`${API_BASE_URL}/customers`, {
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

    const data = await response.json()
    return {
      success: true,
      message: `Applicant ${formData.full_name} onboarded successfully. Loan application ${formData.loan_application_id} recorded.`,
      data,
    }
  } catch (error) {
    console.error("Error onboarding applicant:", error)
    return {
      success: false,
      message: error instanceof Error ? error.message : "Failed to onboard applicant",
    }
  }
}
