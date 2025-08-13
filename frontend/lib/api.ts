const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

export interface HealthStatus {
  status: "healthy" | "unhealthy" | "loading" | "error"
  message?: string
  timestamp: string
}

export async function checkHealth(): Promise<HealthStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/healthz`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (response.ok) {
      return {
        status: "healthy",
        message: "Service is running",
        timestamp: new Date().toISOString(),
      }
    } else {
      return {
        status: "unhealthy",
        message: `HTTP ${response.status}`,
        timestamp: new Date().toISOString(),
      }
    }
  } catch (error) {
    return {
      status: "error",
      message: error instanceof Error ? error.message : "Unknown error",
      timestamp: new Date().toISOString(),
    }
  }
}

export async function checkReadiness(): Promise<HealthStatus> {
  try {
    const response = await fetch(`${API_BASE_URL}/readyz`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (response.ok) {
      return {
        status: "healthy",
        message: "Service is ready",
        timestamp: new Date().toISOString(),
      }
    } else {
      return {
        status: "unhealthy",
        message: `HTTP ${response.status}`,
        timestamp: new Date().toISOString(),
      }
    }
  } catch (error) {
    return {
      status: "error",
      message: error instanceof Error ? error.message : "Unknown error",
      timestamp: new Date().toISOString(),
    }
  }
}

export function getMetricsUrl(): string {
  return `${API_BASE_URL}/metrics`
}
