import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { CheckCircle, XCircle, AlertCircle } from "lucide-react"
import { LoadingSpinner } from "./loading-spinner"
import type { HealthStatus } from "@/lib/api"

interface StatusCardProps {
  title: string
  status: HealthStatus
  isLoading?: boolean
}

export function StatusCard({ title, status, isLoading }: StatusCardProps) {
  const getStatusIcon = () => {
    if (isLoading) {
      return <LoadingSpinner size="sm" />
    }

    switch (status.status) {
      case "healthy":
        return <CheckCircle className="h-5 w-5 text-green-600 animate-pulse" />
      case "unhealthy":
        return <XCircle className="h-5 w-5 text-red-600 animate-bounce" />
      case "error":
        return <AlertCircle className="h-5 w-5 text-red-600 animate-pulse" />
      default:
        return <AlertCircle className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusBadge = () => {
    if (isLoading) {
      return (
        <Badge variant="secondary" className="animate-pulse">
          Checking...
        </Badge>
      )
    }

    switch (status.status) {
      case "healthy":
        return (
          <Badge className="bg-green-100 text-green-800 hover:bg-green-200 transition-colors duration-300 hover:scale-105 transform">
            Healthy
          </Badge>
        )
      case "unhealthy":
        return (
          <Badge className="bg-red-100 text-red-800 hover:bg-red-200 transition-colors duration-300 hover:scale-105 transform">
            Unhealthy
          </Badge>
        )
      case "error":
        return (
          <Badge className="bg-red-100 text-red-800 hover:bg-red-200 transition-colors duration-300 hover:scale-105 transform">
            Error
          </Badge>
        )
      default:
        return <Badge variant="secondary">Unknown</Badge>
    }
  }

  const getCardBorderColor = () => {
    switch (status.status) {
      case "healthy":
        return "border-l-4 border-l-green-500"
      case "unhealthy":
      case "error":
        return "border-l-4 border-l-red-500"
      default:
        return "border-l-4 border-l-gray-300"
    }
  }

  return (
    <Card
      className={`group hover:shadow-lg hover:scale-105 transition-all duration-300 cursor-pointer ${getCardBorderColor()}`}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium font-montserrat">{title}</CardTitle>
        <div className="group-hover:scale-110 transition-transform duration-300">{getStatusIcon()}</div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-between">
          {getStatusBadge()}
          <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors duration-300">
            {new Date(status.timestamp).toLocaleTimeString()}
          </span>
        </div>
        {status.message && (
          <p className="text-xs text-muted-foreground mt-2 group-hover:text-foreground transition-colors duration-300">
            {status.message}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
