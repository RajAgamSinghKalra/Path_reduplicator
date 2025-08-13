import type { CustomerFormData } from "./customer-api"

const STORAGE_KEY = "reduplicator_last_customer"

export function saveCustomerData(data: CustomerFormData): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
  } catch (error) {
    console.warn("Failed to save customer data to localStorage:", error)
  }
}

export function loadCustomerData(): Partial<CustomerFormData> | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : null
  } catch (error) {
    console.warn("Failed to load customer data from localStorage:", error)
    return null
  }
}

export function clearCustomerData(): void {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (error) {
    console.warn("Failed to clear customer data from localStorage:", error)
  }
}
