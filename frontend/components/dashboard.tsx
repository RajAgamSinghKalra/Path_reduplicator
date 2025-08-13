"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusCard } from "./status-card"
import { AnimatedContainer } from "./animated-container"
import { LoadingSpinner } from "./loading-spinner"
import {
  checkHealth,
  checkReadiness,
  getMetricsUrl,
  getStats,
  type HealthStatus,
} from "@/lib/api"
import { ExternalLink, RefreshCw, Activity, Users, AlertTriangle, TrendingUp, Building2 } from "lucide-react"

interface LoanMetrics {
  totalApplicants: number
  todayApplicants: number
  duplicateAlerts: number
  highRiskDuplicates: number
  processingRate: number
  lastUpdated: string
}

export function Dashboard() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus>({
    status: "loading",
    timestamp: new Date().toISOString(),
  })
  const [readinessStatus, setReadinessStatus] = useState<HealthStatus>({
    status: "loading",
    timestamp: new Date().toISOString(),
  })
  const [isLoading, setIsLoading] = useState(false)

  const [loanMetrics, setLoanMetrics] = useState<LoanMetrics>({
    totalApplicants: 0,
    todayApplicants: 0,
    duplicateAlerts: 0,
    highRiskDuplicates: 0,
    processingRate: 0,
    lastUpdated: "",
  })

  const checkStatuses = async () => {
    setIsLoading(true)
    try {
      const [health, readiness, stats] = await Promise.all([
        checkHealth(),
        checkReadiness(),
        getStats(),
      ])
      setHealthStatus(health)
      setReadinessStatus(readiness)
      setLoanMetrics({
        totalApplicants: stats.total_applicants,
        todayApplicants: stats.today_applicants,
        duplicateAlerts: stats.duplicate_alerts,
        highRiskDuplicates: stats.high_risk_duplicates,
        processingRate: stats.processing_rate,
        lastUpdated: new Date().toLocaleString(),
      })
    } catch (error) {
      console.error("Error checking statuses:", error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    checkStatuses()
    // Auto-refresh every 30 seconds
    const interval = setInterval(checkStatuses, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="space-y-6">
      <AnimatedContainer animation="fade-in">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card className="group hover:shadow-lg hover:scale-105 transition-all duration-300 cursor-pointer border-l-4 border-l-secondary">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium font-montserrat">Total Applicants</CardTitle>
              <Users className="h-5 w-5 text-secondary group-hover:scale-110 transition-transform duration-300" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-primary font-montserrat">
                {loanMetrics.totalApplicants.toLocaleString()}
              </div>
              <p className="text-xs text-muted-foreground">+{loanMetrics.todayApplicants} today</p>
            </CardContent>
          </Card>

          <Card className="group hover:shadow-lg hover:scale-105 transition-all duration-300 cursor-pointer border-l-4 border-l-accent">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium font-montserrat">Duplicate Alerts</CardTitle>
              <AlertTriangle className="h-5 w-5 text-accent group-hover:scale-110 transition-transform duration-300" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-accent font-montserrat">{loanMetrics.duplicateAlerts}</div>
              <p className="text-xs text-muted-foreground">{loanMetrics.highRiskDuplicates} high risk</p>
            </CardContent>
          </Card>

          <Card className="group hover:shadow-lg hover:scale-105 transition-all duration-300 cursor-pointer border-l-4 border-l-secondary">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium font-montserrat">Processing Rate</CardTitle>
              <TrendingUp className="h-5 w-5 text-secondary group-hover:scale-110 transition-transform duration-300" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-secondary font-montserrat">{loanMetrics.processingRate}%</div>
              <p className="text-xs text-muted-foreground">System efficiency</p>
            </CardContent>
          </Card>

          <Card className="group hover:shadow-lg hover:scale-105 transition-all duration-300 cursor-pointer border-l-4 border-l-primary">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium font-montserrat">Branch Operations</CardTitle>
              <Building2 className="h-5 w-5 text-primary group-hover:scale-110 transition-transform duration-300" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-primary font-montserrat">Active</div>
              <p className="text-xs text-muted-foreground">All systems operational</p>
            </CardContent>
          </Card>
        </div>
      </AnimatedContainer>

      <AnimatedContainer animation="slide-up" delay={200}>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <StatusCard title="Health Check" status={healthStatus} isLoading={isLoading} />
          <StatusCard title="Readiness Check" status={readinessStatus} isLoading={isLoading} />
          <Card className="group hover:shadow-lg transition-all duration-300">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium font-montserrat">System Metrics</CardTitle>
              <Activity className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors duration-300" />
            </CardHeader>
            <CardContent>
              <Button
                variant="outline"
                size="sm"
                className="w-full bg-transparent hover:bg-primary hover:text-primary-foreground transition-all duration-300 hover:scale-105"
                onClick={() => window.open(getMetricsUrl(), "_blank")}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View Prometheus Metrics
              </Button>
            </CardContent>
          </Card>
        </div>
      </AnimatedContainer>

      <AnimatedContainer animation="slide-up" delay={400}>
        <Card className="hover:shadow-lg transition-all duration-300">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 font-montserrat">
              <RefreshCw className="h-5 w-5" />
              System Actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 flex-wrap">
              <Button
                onClick={checkStatuses}
                disabled={isLoading}
                variant="outline"
                className="hover:scale-105 transition-all duration-300 bg-transparent"
              >
                {isLoading ? <LoadingSpinner size="sm" className="mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                Refresh Status
              </Button>
              <Button variant="secondary" size="sm" className="hover:scale-105 transition-all duration-300">
                <AlertTriangle className="h-4 w-4 mr-2" />
                Review Alerts
              </Button>
            </div>
            <div className="mt-4 text-sm text-muted-foreground">Last updated: {loanMetrics.lastUpdated}</div>
          </CardContent>
        </Card>
      </AnimatedContainer>

      <AnimatedContainer animation="fade-in" delay={600}>
        <Card className="hover:shadow-lg transition-all duration-300">
          <CardHeader>
            <CardTitle className="font-montserrat">API Configuration</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { label: "Base URL", value: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000" },
                { label: "Health Endpoint", value: "/healthz" },
                { label: "Readiness Endpoint", value: "/readyz" },
                { label: "Metrics Endpoint", value: "/metrics" },
              ].map((item, index) => (
                <div key={item.label} className="flex justify-between items-center group">
                  <span className="text-muted-foreground text-sm">{item.label}:</span>
                  <code className="bg-muted px-3 py-1 rounded-md text-xs font-mono group-hover:bg-primary/10 transition-colors duration-300">
                    {item.value}
                  </code>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </AnimatedContainer>
    </div>
  )
}
