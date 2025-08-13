"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import {
  AlertTriangle,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  User,
  MapPin,
  CreditCard,
  Building2,
} from "lucide-react"
import { useState } from "react"
import type { LoanDuplicateCheckResponse, LoanCandidateMatch } from "@/lib/loan-duplicate-api"

interface LoanDuplicateResultsProps {
  results: LoanDuplicateCheckResponse
}

export function LoanDuplicateResults({ results }: LoanDuplicateResultsProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [sortField, setSortField] = useState<keyof LoanCandidateMatch>("score")
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc")

  const toggleRowExpansion = (customerId: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(customerId)) {
      newExpanded.delete(customerId)
    } else {
      newExpanded.add(customerId)
    }
    setExpandedRows(newExpanded)
  }

  const handleSort = (field: keyof LoanCandidateMatch) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc")
    } else {
      setSortField(field)
      setSortDirection("desc")
    }
  }

  const sortedCandidates = [...results.candidates].sort((a, b) => {
    const aValue = a[sortField]
    const bValue = b[sortField]

    if (typeof aValue === "number" && typeof bValue === "number") {
      return sortDirection === "asc" ? aValue - bValue : bValue - aValue
    }

    const aStr = String(aValue).toLowerCase()
    const bStr = String(bValue).toLowerCase()
    return sortDirection === "asc" ? aStr.localeCompare(bStr) : bStr.localeCompare(aStr)
  })

  const isHighRisk = results.score >= results.threshold

  return (
    <div className="space-y-6">
      {/* Verdict Card */}
      <Card className={`border-2 max-w-4xl mx-auto ${isHighRisk ? "border-accent" : "border-secondary"}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {isHighRisk ? (
              <AlertTriangle className="h-6 w-6 text-accent" />
            ) : (
              <CheckCircle className="h-6 w-6 text-secondary" />
            )}
            Loan Duplicate Detection Result
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div>
              <Badge
                className={
                  isHighRisk
                    ? "bg-accent text-accent-foreground hover:bg-accent/90"
                    : "bg-secondary text-secondary-foreground hover:bg-secondary/90"
                }
              >
                {results.is_duplicate ? "DUPLICATE DETECTED" : "UNIQUE APPLICANT"}
              </Badge>
              {isHighRisk && (
                <Badge variant="destructive" className="ml-2">
                  HIGH RISK
                </Badge>
              )}
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{(results.score * 100).toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">Similarity Score</div>
            </div>
          </div>
          <div className="text-sm text-muted-foreground">
            Risk Threshold: {(results.threshold * 100).toFixed(0)}% • Found {results.candidates.length} potential
            matches
          </div>
        </CardContent>
      </Card>

      {/* Best Match Card */}
      {results.best_match && (
        <Card className="max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Best Match
              {results.best_match.score >= results.threshold && (
                <Badge className="bg-accent text-accent-foreground">WARNING</Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-6 md:grid-cols-2">
              {/* Identity Information */}
              <div className="space-y-3">
                <h4 className="font-medium text-primary flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Identity Details
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Name:</span>
                    <span className="font-medium">{results.best_match.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Date of Birth:</span>
                    <span className="font-medium">{results.best_match.date_of_birth}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Phone:</span>
                    <span className="font-medium">{results.best_match.phone}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Email:</span>
                    <span className="font-medium">{results.best_match.email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Government ID:</span>
                    <span className="font-medium">{results.best_match.government_id}</span>
                  </div>
                </div>
              </div>

                {/* Match Details */}
                <div className="space-y-3">
                  <h4 className="font-medium text-primary flex items-center gap-2">
                    <CreditCard className="h-4 w-4" />
                    Match Details
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Match Score:</span>
                      <Badge
                        variant="outline"
                        className={results.best_match.score >= results.threshold ? "border-accent text-accent" : ""}
                      >
                        {(results.best_match.score * 100).toFixed(1)}%
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Vector Distance:</span>
                      <span className="font-mono text-sm">{results.best_match.vector_distance.toFixed(4)}</span>
                    </div>
                  </div>
                </div>
            </div>

            {/* Address Information */}
            <div className="mt-6 pt-4 border-t">
              <h4 className="font-medium text-primary flex items-center gap-2 mb-3">
                <Building2 className="h-4 w-4" />
                Address Information
              </h4>
              <div className="grid gap-2 md:grid-cols-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Address:</span>
                  <span className="font-medium text-right">{results.best_match.address_line}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">City:</span>
                  <span className="font-medium">{results.best_match.city}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">State:</span>
                  <span className="font-medium">{results.best_match.state}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Postal Code:</span>
                  <span className="font-medium">{results.best_match.postal_code}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Candidates Table */}
      {results.candidates.length > 0 && (
        <Card className="max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle>Top {Math.min(10, results.candidates.length)} Candidate Matches</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[50px]"></TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort("name")}
                      className="h-auto p-0 font-semibold"
                    >
                      Name {sortField === "name" && (sortDirection === "asc" ? "↑" : "↓")}
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort("date_of_birth")}
                      className="h-auto p-0 font-semibold"
                    >
                      DOB {sortField === "date_of_birth" && (sortDirection === "asc" ? "↑" : "↓")}
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort("phone")}
                      className="h-auto p-0 font-semibold"
                    >
                      Phone {sortField === "phone" && (sortDirection === "asc" ? "↑" : "↓")}
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort("score")}
                      className="h-auto p-0 font-semibold"
                    >
                      Score {sortField === "score" && (sortDirection === "asc" ? "↑" : "↓")}
                    </Button>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedCandidates.slice(0, 10).map((candidate) => (
                  <Collapsible key={candidate.customer_id} asChild>
                    <>
                      <CollapsibleTrigger asChild>
                        <TableRow
                          className="cursor-pointer hover:bg-muted/50"
                          onClick={() => toggleRowExpansion(candidate.customer_id)}
                        >
                          <TableCell>
                            {expandedRows.has(candidate.customer_id) ? (
                              <ChevronDown className="h-4 w-4" />
                            ) : (
                              <ChevronRight className="h-4 w-4" />
                            )}
                          </TableCell>
                          <TableCell className="font-medium">{candidate.name}</TableCell>
                          <TableCell>{candidate.date_of_birth}</TableCell>
                          <TableCell>{candidate.phone}</TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={
                                candidate.score >= results.threshold
                                  ? "border-accent text-accent"
                                  : "border-secondary text-secondary"
                              }
                            >
                              {(candidate.score * 100).toFixed(1)}%
                            </Badge>
                          </TableCell>
                        </TableRow>
                      </CollapsibleTrigger>
                      <CollapsibleContent asChild>
                        <TableRow>
                          <TableCell colSpan={5} className="bg-muted/20">
                            <div className="p-4 space-y-4">
                              <div className="grid gap-4 md:grid-cols-2">
                                {/* Identity & Address */}
                                <div>
                                  <div className="flex items-center gap-2 mb-2">
                                    <MapPin className="h-4 w-4 text-muted-foreground" />
                                    <span className="font-medium text-sm">Identity & Address</span>
                                  </div>
                                  <div className="grid gap-1 text-xs">
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Email:</span>
                                      <span>{candidate.email}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Government ID:</span>
                                      <span>{candidate.government_id}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Address:</span>
                                      <span className="text-right">{candidate.address_line}</span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">City, State:</span>
                                      <span>
                                        {candidate.city}, {candidate.state}
                                      </span>
                                    </div>
                                    <div className="flex justify-between">
                                      <span className="text-muted-foreground">Postal Code:</span>
                                      <span>{candidate.postal_code}</span>
                                    </div>
                                  </div>
                                </div>

                                  {/* Match Details */}
                                  <div>
                                    <div className="flex items-center gap-2 mb-2">
                                      <CreditCard className="h-4 w-4 text-muted-foreground" />
                                      <span className="font-medium text-sm">Match Details</span>
                                    </div>
                                    <div className="grid gap-1 text-xs">
                                      <div className="flex justify-between">
                                        <span className="text-muted-foreground">Vector Distance:</span>
                                        <span className="font-mono">{candidate.vector_distance.toFixed(4)}</span>
                                      </div>
                                    </div>
                                  </div>
                              </div>
                            </div>
                          </TableCell>
                        </TableRow>
                      </CollapsibleContent>
                    </>
                  </Collapsible>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
