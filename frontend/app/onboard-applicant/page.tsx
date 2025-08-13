import { ApplicantForm } from "@/components/applicant-form"
import { LayoutWrapper } from "@/components/layout-wrapper"

export default function OnboardApplicantPage() {
  return (
    <LayoutWrapper>
      <div className="container mx-auto py-8 px-4">
        <div className="max-w-4xl mx-auto">
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-primary mb-2">Onboard New Loan Applicant</h1>
            <p className="text-muted-foreground">
              Complete the form below to onboard a new loan applicant into the system
            </p>
          </div>
          <ApplicantForm />
        </div>
      </div>
    </LayoutWrapper>
  )
}
