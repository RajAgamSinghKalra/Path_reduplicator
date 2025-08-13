import { LayoutWrapper } from "@/components/layout-wrapper"
import { Dashboard } from "@/components/dashboard"
import { AnimatedContainer } from "@/components/animated-container"

export default function HomePage() {
  return (
    <LayoutWrapper
      title="Dashboard"
      description="Monitor system health and access metrics for the Reduplicator service"
    >
      <AnimatedContainer animation="fade-in">
        <div className="mb-6">
          <h1 className="text-3xl font-bold font-montserrat text-primary mb-2">Welcome to Loan Dedupe Portal</h1>
          <p className="text-muted-foreground font-open-sans">Your comprehensive banking duplicate detection system</p>
        </div>
        <Dashboard />
      </AnimatedContainer>
    </LayoutWrapper>
  )
}
