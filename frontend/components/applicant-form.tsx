"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import { Loader2, Save, UserPlus, Building2, CreditCard } from "lucide-react"
import {
  onboardApplicant,
  validateEmail,
  validateE164Phone,
  validatePostalCode,
  validateDateOfBirth,
  validateNumericAmount,
  type ApplicantFormData,
} from "@/lib/applicant-api"
import { saveApplicantData, loadApplicantData } from "@/lib/applicant-storage"

const initialFormData: ApplicantFormData = {
  full_name: "",
  date_of_birth: "",
  phone: "",
  email: "",
  government_id: "",
  address_line: "",
  city: "",
  state: "",
  postal_code: "",
  country: "IN",
  account_number: "",
  loan_application_id: "",
  requested_amount: "",
  loan_type: "",
  branch_code: "",
}

const loanTypes = ["Personal Loan", "Home Loan", "Car Loan", "Business Loan", "Education Loan", "Gold Loan"]

interface FormErrors {
  [key: string]: string
}

export function ApplicantForm() {
  const [formData, setFormData] = useState<ApplicantFormData>(initialFormData)
  const [errors, setErrors] = useState<FormErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { toast } = useToast()

  // Load saved data on component mount
  useEffect(() => {
    const savedData = loadApplicantData()
    if (savedData) {
      setFormData({ ...initialFormData, ...savedData })
    }
  }, [])

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Required identity field validation
    if (!formData.full_name.trim()) newErrors.full_name = "Full name is required"
    if (!formData.date_of_birth) newErrors.date_of_birth = "Date of birth is required"
    if (!formData.phone.trim()) newErrors.phone = "Phone number is required"
    if (!formData.email.trim()) newErrors.email = "Email is required"
    if (!formData.government_id.trim()) newErrors.government_id = "Government ID is required"
    if (!formData.address_line.trim()) newErrors.address_line = "Address is required"
    if (!formData.city.trim()) newErrors.city = "City is required"
    if (!formData.state.trim()) newErrors.state = "State is required"
    if (!formData.postal_code.trim()) newErrors.postal_code = "Postal code is required"

    // Required loan field validation
    if (!formData.loan_application_id.trim()) newErrors.loan_application_id = "Loan application ID is required"
    if (!formData.requested_amount.trim()) newErrors.requested_amount = "Requested amount is required"
    if (!formData.loan_type.trim()) newErrors.loan_type = "Loan type is required"
    if (!formData.branch_code.trim()) newErrors.branch_code = "Branch code is required"

    // Format validation
    if (formData.email && !validateEmail(formData.email)) {
      newErrors.email = "Please enter a valid email address"
    }

    if (formData.phone && !validateE164Phone(formData.phone)) {
      newErrors.phone = "Please enter a valid E.164 phone number (e.g., +911234567890)"
    }

    if (formData.postal_code && !validatePostalCode(formData.postal_code)) {
      newErrors.postal_code = "Please enter a valid 6-digit postal code"
    }

    if (formData.date_of_birth && !validateDateOfBirth(formData.date_of_birth)) {
      newErrors.date_of_birth = "Please enter a valid date (YYYY-MM-DD)"
    }

    if (formData.requested_amount && !validateNumericAmount(formData.requested_amount)) {
      newErrors.requested_amount = "Please enter a valid amount (e.g., 100000.00)"
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (field: keyof ApplicantFormData, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      toast({
        title: "Validation Error",
        description: "Please fix the errors in the form",
        variant: "destructive",
      })
      return
    }

    setIsSubmitting(true)

    try {
      const result = await onboardApplicant(formData)

      if (result.success) {
        toast({
          title: "Success",
          description: result.message,
        })
        // Save to localStorage for convenience
        saveApplicantData(formData)
        // Reset form
        setFormData(initialFormData)
      } else {
        toast({
          title: "Error",
          description: result.message,
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to onboard applicant. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Card className="max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-primary">
          <UserPlus className="h-5 w-5" />
          Onboard New Loan Applicant
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Personal Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-primary flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              Personal Information
            </h3>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name *</Label>
                <Input
                  id="full_name"
                  value={formData.full_name}
                  onChange={(e) => handleInputChange("full_name", e.target.value)}
                  className={errors.full_name ? "border-destructive" : ""}
                />
                {errors.full_name && <p className="text-sm text-destructive">{errors.full_name}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="date_of_birth">Date of Birth (YYYY-MM-DD) *</Label>
                <Input
                  id="date_of_birth"
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => handleInputChange("date_of_birth", e.target.value)}
                  className={errors.date_of_birth ? "border-destructive" : ""}
                />
                {errors.date_of_birth && <p className="text-sm text-destructive">{errors.date_of_birth}</p>}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="phone">Phone (E.164 format) *</Label>
                <Input
                  id="phone"
                  placeholder="+911234567890"
                  value={formData.phone}
                  onChange={(e) => handleInputChange("phone", e.target.value)}
                  className={errors.phone ? "border-destructive" : ""}
                />
                {errors.phone && <p className="text-sm text-destructive">{errors.phone}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email *</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange("email", e.target.value)}
                  className={errors.email ? "border-destructive" : ""}
                />
                {errors.email && <p className="text-sm text-destructive">{errors.email}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="government_id">Government ID *</Label>
              <Input
                id="government_id"
                placeholder="Aadhaar, PAN, Passport, etc."
                value={formData.government_id}
                onChange={(e) => handleInputChange("government_id", e.target.value)}
                className={errors.government_id ? "border-destructive" : ""}
              />
              {errors.government_id && <p className="text-sm text-destructive">{errors.government_id}</p>}
            </div>
          </div>

          {/* Address Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-primary flex items-center gap-2">
              <Building2 className="h-5 w-5" />
              Address Information
            </h3>

            <div className="space-y-2">
              <Label htmlFor="address_line">Address Line *</Label>
              <Input
                id="address_line"
                value={formData.address_line}
                onChange={(e) => handleInputChange("address_line", e.target.value)}
                className={errors.address_line ? "border-destructive" : ""}
              />
              {errors.address_line && <p className="text-sm text-destructive">{errors.address_line}</p>}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="city">City *</Label>
                <Input
                  id="city"
                  value={formData.city}
                  onChange={(e) => handleInputChange("city", e.target.value)}
                  className={errors.city ? "border-destructive" : ""}
                />
                {errors.city && <p className="text-sm text-destructive">{errors.city}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="state">State *</Label>
                <Input
                  id="state"
                  value={formData.state}
                  onChange={(e) => handleInputChange("state", e.target.value)}
                  className={errors.state ? "border-destructive" : ""}
                />
                {errors.state && <p className="text-sm text-destructive">{errors.state}</p>}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="postal_code">Postal Code (6 digits) *</Label>
                <Input
                  id="postal_code"
                  placeholder="123456"
                  value={formData.postal_code}
                  onChange={(e) => handleInputChange("postal_code", e.target.value)}
                  className={errors.postal_code ? "border-destructive" : ""}
                />
                {errors.postal_code && <p className="text-sm text-destructive">{errors.postal_code}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="country">Country *</Label>
                <Select value={formData.country} onValueChange={(value) => handleInputChange("country", value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="IN">India</SelectItem>
                    <SelectItem value="US">United States</SelectItem>
                    <SelectItem value="GB">United Kingdom</SelectItem>
                    <SelectItem value="CA">Canada</SelectItem>
                    <SelectItem value="AU">Australia</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Loan Information */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-primary flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Loan Information
            </h3>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="account_number">Account Number</Label>
                <Input
                  id="account_number"
                  placeholder="Existing account number (if any)"
                  value={formData.account_number}
                  onChange={(e) => handleInputChange("account_number", e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="loan_application_id">Loan Application ID *</Label>
                <Input
                  id="loan_application_id"
                  placeholder="LA2024001234"
                  value={formData.loan_application_id}
                  onChange={(e) => handleInputChange("loan_application_id", e.target.value)}
                  className={errors.loan_application_id ? "border-destructive" : ""}
                />
                {errors.loan_application_id && <p className="text-sm text-destructive">{errors.loan_application_id}</p>}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="requested_amount">Requested Amount (₹) *</Label>
                <Input
                  id="requested_amount"
                  placeholder="500000.00"
                  value={formData.requested_amount}
                  onChange={(e) => handleInputChange("requested_amount", e.target.value)}
                  className={errors.requested_amount ? "border-destructive" : ""}
                />
                {errors.requested_amount && <p className="text-sm text-destructive">{errors.requested_amount}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="loan_type">Loan Type *</Label>
                <Select value={formData.loan_type} onValueChange={(value) => handleInputChange("loan_type", value)}>
                  <SelectTrigger className={errors.loan_type ? "border-destructive" : ""}>
                    <SelectValue placeholder="Select loan type" />
                  </SelectTrigger>
                  <SelectContent>
                    {loanTypes.map((type) => (
                      <SelectItem key={type} value={type}>
                        {type}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.loan_type && <p className="text-sm text-destructive">{errors.loan_type}</p>}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="branch_code">Branch Code *</Label>
              <Input
                id="branch_code"
                placeholder="BR001"
                value={formData.branch_code}
                onChange={(e) => handleInputChange("branch_code", e.target.value)}
                className={errors.branch_code ? "border-destructive" : ""}
              />
              {errors.branch_code && <p className="text-sm text-destructive">{errors.branch_code}</p>}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex gap-4 pt-4">
            <Button
              type="submit"
              disabled={isSubmitting}
              className="bg-secondary text-secondary-foreground hover:bg-secondary/90"
            >
              {isSubmitting ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
              {isSubmitting ? "Onboarding Applicant..." : "Onboard Applicant"}
            </Button>

            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setFormData(initialFormData)
                setErrors({})
              }}
            >
              Clear Form
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  )
}
