"use client"

import type React from "react"
import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useToast } from "@/hooks/use-toast"
import { Loader2, Search, UserCheck } from "lucide-react"
import { checkDuplicate, type DuplicateCheckRequest, type DuplicateCheckResponse } from "@/lib/duplicate-api"
import { validateEmail, validateE164Phone, validatePostalCode, validateDateOfBirth } from "@/lib/customer-api"
import { loadCustomerData } from "@/lib/storage"
import { DuplicateResults } from "./duplicate-results"

const initialFormData: DuplicateCheckRequest = {
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
}

interface FormErrors {
  [key: string]: string
}

export function DuplicateCheckForm() {
  const [formData, setFormData] = useState<DuplicateCheckRequest>(initialFormData)
  const [errors, setErrors] = useState<FormErrors>({})
  const [isChecking, setIsChecking] = useState(false)
  const [results, setResults] = useState<DuplicateCheckResponse | null>(null)
  const { toast } = useToast()

  // Load saved data on component mount
  useEffect(() => {
    const savedData = loadCustomerData()
    if (savedData) {
      setFormData({ ...initialFormData, ...savedData })
    }
  }, [])

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}

    // Required field validation
    if (!formData.full_name.trim()) newErrors.full_name = "Full name is required"
    if (!formData.date_of_birth) newErrors.date_of_birth = "Date of birth is required"
    if (!formData.phone.trim()) newErrors.phone = "Phone number is required"
    if (!formData.email.trim()) newErrors.email = "Email is required"
    if (!formData.government_id.trim()) newErrors.government_id = "Government ID is required"
    if (!formData.address_line.trim()) newErrors.address_line = "Address is required"
    if (!formData.city.trim()) newErrors.city = "City is required"
    if (!formData.state.trim()) newErrors.state = "State is required"
    if (!formData.postal_code.trim()) newErrors.postal_code = "Postal code is required"

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

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleInputChange = (field: keyof DuplicateCheckRequest, value: string) => {
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

    setIsChecking(true)
    setResults(null)

    try {
      const result = await checkDuplicate(formData)

      if (result.success && result.data) {
        setResults(result.data)
        toast({
          title: "Duplicate Check Complete",
          description: result.data.is_duplicate
            ? `Duplicate detected with ${(result.data.score * 100).toFixed(1)}% similarity`
            : "No duplicates found",
        })
      } else {
        toast({
          title: "Error",
          description: result.message || "Failed to check for duplicates",
          variant: "destructive",
        })
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to check for duplicates. Please try again.",
        variant: "destructive",
      })
    } finally {
      setIsChecking(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card className="max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <UserCheck className="h-5 w-5" />
            Duplicate Customer Check
          </CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Personal Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-midnight-blue">Personal Information</h3>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name *</Label>
                  <Input
                    id="full_name"
                    value={formData.full_name}
                    onChange={(e) => handleInputChange("full_name", e.target.value)}
                    className={errors.full_name ? "border-coral-red" : ""}
                  />
                  {errors.full_name && <p className="text-sm text-coral-red">{errors.full_name}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="date_of_birth">Date of Birth (YYYY-MM-DD) *</Label>
                  <Input
                    id="date_of_birth"
                    type="date"
                    value={formData.date_of_birth}
                    onChange={(e) => handleInputChange("date_of_birth", e.target.value)}
                    className={errors.date_of_birth ? "border-coral-red" : ""}
                  />
                  {errors.date_of_birth && <p className="text-sm text-coral-red">{errors.date_of_birth}</p>}
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
                    className={errors.phone ? "border-coral-red" : ""}
                  />
                  {errors.phone && <p className="text-sm text-coral-red">{errors.phone}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => handleInputChange("email", e.target.value)}
                    className={errors.email ? "border-coral-red" : ""}
                  />
                  {errors.email && <p className="text-sm text-coral-red">{errors.email}</p>}
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="government_id">Government ID *</Label>
                <Input
                  id="government_id"
                  value={formData.government_id}
                  onChange={(e) => handleInputChange("government_id", e.target.value)}
                  className={errors.government_id ? "border-coral-red" : ""}
                />
                {errors.government_id && <p className="text-sm text-coral-red">{errors.government_id}</p>}
              </div>
            </div>

            {/* Address Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-medium text-midnight-blue">Address Information</h3>

              <div className="space-y-2">
                <Label htmlFor="address_line">Address Line *</Label>
                <Input
                  id="address_line"
                  value={formData.address_line}
                  onChange={(e) => handleInputChange("address_line", e.target.value)}
                  className={errors.address_line ? "border-coral-red" : ""}
                />
                {errors.address_line && <p className="text-sm text-coral-red">{errors.address_line}</p>}
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="city">City *</Label>
                  <Input
                    id="city"
                    value={formData.city}
                    onChange={(e) => handleInputChange("city", e.target.value)}
                    className={errors.city ? "border-coral-red" : ""}
                  />
                  {errors.city && <p className="text-sm text-coral-red">{errors.city}</p>}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="state">State *</Label>
                  <Input
                    id="state"
                    value={formData.state}
                    onChange={(e) => handleInputChange("state", e.target.value)}
                    className={errors.state ? "border-coral-red" : ""}
                  />
                  {errors.state && <p className="text-sm text-coral-red">{errors.state}</p>}
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
                    className={errors.postal_code ? "border-coral-red" : ""}
                  />
                  {errors.postal_code && <p className="text-sm text-coral-red">{errors.postal_code}</p>}
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

            {/* Submit Button */}
            <div className="flex gap-4 pt-4">
              <Button
                type="submit"
                disabled={isChecking}
                className="bg-soft-sky text-midnight-blue hover:bg-soft-sky/90"
              >
                {isChecking ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Search className="h-4 w-4 mr-2" />}
                {isChecking ? "Checking for Duplicates..." : "Check for Duplicates"}
              </Button>

              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setFormData(initialFormData)
                  setErrors({})
                  setResults(null)
                }}
              >
                Clear Form
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      {results && <DuplicateResults results={results} />}
    </div>
  )
}
