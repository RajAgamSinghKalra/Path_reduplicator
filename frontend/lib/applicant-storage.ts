import type { ApplicantFormData } from "./applicant-api"

const STORAGE_KEY = "loan_applicant_data"

export const saveApplicantData = (data: ApplicantFormData): void => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (error) {
    console.error("Failed to save applicant data:", error)
  }
}

export const loadApplicantData = (): Partial<ApplicantFormData> | null => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? JSON.parse(saved) : null
  } catch (error) {
    console.error("Failed to load applicant data:", error)
    return null
  }
}

export const clearApplicantData = (): void => {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (error) {
    console.error("Failed to clear applicant data:", error)
  }
}
