const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export interface Customer {
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

export interface CustomerFormData extends Customer {}

export interface CustomerResponse {
  success: boolean
  message: string
  customer_id?: string
}

export async function addCustomer(customer: CustomerFormData): Promise<CustomerResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/customers`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(customer),
    })

    const data = await response.json()

    if (response.ok) {
      return {
        success: true,
        message: "Customer added successfully",
        customer_id: data.customer_id,
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

// Validation functions
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

export function validateE164Phone(phone: string): boolean {
  const e164Regex = /^\+[1-9]\d{1,14}$/
  return e164Regex.test(phone)
}

export function validatePostalCode(postalCode: string): boolean {
  const postalRegex = /^\d{6}$/
  return postalRegex.test(postalCode)
}

export function validateDateOfBirth(dob: string): boolean {
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/
  if (!dateRegex.test(dob)) return false

  const date = new Date(dob)
  const today = new Date()
  return date <= today && date.getFullYear() > 1900
}
