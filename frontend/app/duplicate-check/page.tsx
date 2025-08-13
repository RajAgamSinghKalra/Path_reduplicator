import { LayoutWrapper } from "@/components/layout-wrapper"
import { LoanDuplicateCheckForm } from "@/components/loan-duplicate-check-form"

export default function DuplicateCheckPage() {
  return (
    <LayoutWrapper
      title="Loan Applicant Duplicate Check"
      description="Check if a loan applicant already exists in the system with advanced similarity matching and compliance review"
    >
      <LoanDuplicateCheckForm />
    </LayoutWrapper>
  )
}
