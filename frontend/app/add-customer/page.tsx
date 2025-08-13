import { LayoutWrapper } from "@/components/layout-wrapper"
import { CustomerForm } from "@/components/customer-form"

export default function AddCustomerPage() {
  return (
    <LayoutWrapper title="Add Customer" description="Add a new customer to the system with comprehensive validation">
      <CustomerForm />
    </LayoutWrapper>
  )
}
