"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { AlertTriangle, CheckCircle, ChevronDown, ChevronRight, User, MapPin } from "lucide-react"
import { useState } from "react"
import type { DuplicateCheckResponse, CandidateMatch } from "@/lib/duplicate-api"

interface DuplicateResultsProps {
  results: DuplicateCheckResponse
}

export function DuplicateResults({ results }: DuplicateResultsProps) {
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [sortField, setSortField] = useState<keyof CandidateMatch>("score")
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

  const handleSort = (field: keyof CandidateMatch) => {
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
      <Card className={`border-2 ${isHighRisk ? "border-coral-red" : "border-soft-sky"}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {isHighRisk ? (
              <AlertTriangle className="h-6 w-6 text-coral-red" />
            ) : (
              <CheckCircle className="h-6 w-6 text-green-600" />
            )}
            Duplicate Detection Result
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between mb-4">
            <div>
              <Badge
                className={
                  isHighRisk
                    ? "bg-coral-red text-white hover:bg-coral-red/90"
                    : "bg-soft-sky text-midnight-blue hover:bg-soft-sky/90"
                }
              >
                {results.is_duplicate ? "DUPLICATE DETECTED" : "UNIQUE CUSTOMER"}
              </Badge>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold">{(results.score * 100).toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">Similarity Score</div>
            </div>
          </div>
          <div className="text-sm text-muted-foreground">
            Threshold: {(results.threshold * 100).toFixed(0)}% • Found {results.candidates.length} potential matches
          </div>
        </CardContent>
      </Card>

      {/* Best Match Card */}
      {results.best_match && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Best Match
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Name:</span>
                  <span className="font-medium">{results.best_match.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Date of Birth:</span>
                  <span className="font-medium">{results.best_match.date_of_birth}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Phone:</span>
                  <span className="font-medium">{results.best_match.phone}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Email:</span>
                  <span className="font-medium">{results.best_match.email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Government ID:</span>
                  <span className="font-medium">{results.best_match.government_id}</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Address:</span>
                  <span className="font-medium text-right">{results.best_match.address_line}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">City:</span>
                  <span className="font-medium">{results.best_match.city}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">State:</span>
                  <span className="font-medium">{results.best_match.state}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Postal Code:</span>
                  <span className="font-medium">{results.best_match.postal_code}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Score:</span>
                  <Badge variant="outline">{(results.best_match.score * 100).toFixed(1)}%</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Vector Distance:</span>
                  <span className="font-mono text-sm">{results.best_match.vector_distance.toFixed(4)}</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Candidates Table */}
      {results.candidates.length > 0 && (
        <Card>
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
                      onClick={() => handleSort("email")}
                      className="h-auto p-0 font-semibold"
                    >
                      Email {sortField === "email" && (sortDirection === "asc" ? "↑" : "↓")}
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
                          <TableCell>{candidate.email}</TableCell>
                          <TableCell>
                            <Badge
                              variant="outline"
                              className={
                                candidate.score >= results.threshold
                                  ? "border-coral-red text-coral-red"
                                  : "border-soft-sky text-soft-sky"
                              }
                            >
                              {(candidate.score * 100).toFixed(1)}%
                            </Badge>
                          </TableCell>
                        </TableRow>
                      </CollapsibleTrigger>
                      <CollapsibleContent asChild>
                        <TableRow>
                          <TableCell colSpan={6} className="bg-muted/20">
                            <div className="p-4 space-y-2">
                              <div className="flex items-center gap-2 mb-2">
                                <MapPin className="h-4 w-4 text-muted-foreground" />
                                <span className="font-medium">Address Details</span>
                              </div>
                              <div className="grid gap-2 md:grid-cols-2 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Government ID:</span>
                                  <span>{candidate.government_id}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Vector Distance:</span>
                                  <span className="font-mono">{candidate.vector_distance.toFixed(4)}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Address:</span>
                                  <span>{candidate.address_line}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">City:</span>
                                  <span>{candidate.city}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">State:</span>
                                  <span>{candidate.state}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-muted-foreground">Postal Code:</span>
                                  <span>{candidate.postal_code}</span>
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
