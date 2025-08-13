import { LayoutWrapper } from "@/components/layout-wrapper"
import { TrainModelForm } from "@/components/train-model-form"

export default function TrainModelPage() {
  return (
    <LayoutWrapper
      title="Train Model"
      description="Train the duplicate detection model with labeled customer data pairs"
    >
      <TrainModelForm />
    </LayoutWrapper>
  )
}
